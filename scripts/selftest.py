#!/usr/bin/env python3
"""Validate the NaverFinance skill package shape and script basics."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def main() -> int:
    skill_md = ROOT / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    assert "[TODO" not in content, "SKILL.md still contains template TODOs"
    assert re.search(r"^---\nname: naverfinance-web-api\n", content), (
        "frontmatter name missing"
    )
    assert "description: Use" in content, "description should be trigger-focused"
    assert "Never call login" in content, "hard safety rules missing"

    openai_yaml = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    assert "default_prompt:" in openai_yaml, "OpenAI metadata default prompt missing"
    test_skill_description_is_short_and_positive()
    test_public_prompts_do_not_depend_on_dollar_selector()
    test_codex_install_path_uses_agents_skills()
    test_release_checklist_covers_public_skill_surface()

    for script in sorted((ROOT / "scripts").glob("*.py")):
        if script.name in {"naverfinance_api.py", "selftest.py"}:
            continue
        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"{script.name} --help failed: {result.stderr}"

    test_front_json_rejects_error_payload()
    test_request_bytes_rejects_non_public_hosts()
    test_request_bytes_rejects_sensitive_markers()
    test_request_bytes_allows_public_naver_hosts()
    test_theme_and_upjong_tables_are_selected()
    test_group_rows_include_detail_links()
    test_group_detail_stocks_are_selected()
    test_etf_and_etn_api_rows_are_selected()
    test_konex_api_rows_are_selected()
    test_popular_search_menu_path_is_mapped()
    test_new_sise_menu_paths_are_mapped()
    test_investor_program_and_deal_tables_are_selected()
    test_chart_dates_are_validated()
    test_market_index_codes_route_to_pc_tables()
    test_world_hours_rowspan_rows_are_normalized()
    test_stock_trend_mobile_payload_is_selected()
    test_research_relative_detail_links_are_attached()
    test_news_search_requires_query_and_fetches_rows()
    test_home_main_summary_limits_sections()
    test_quote_service_index_query_is_supported()
    test_marketindex_api_prices_are_selected()
    test_marketindex_api_routes_fx_energy_and_metals()
    test_marketindex_rejects_unsafe_api_path_segments()
    test_marketindex_api_prices_reject_error_payloads()
    test_world_prices_use_world_day_json()
    test_dividend_and_etf_use_current_mobile_endpoints()
    test_sector_lists_use_current_mobile_endpoint()
    test_mobile_ranking_fallbacks_mark_reason()
    test_mobile_ranking_rejects_unexpected_rows_shape()

    print("selftest ok")
    return 0


def test_front_json_rejects_error_payload() -> None:
    import naverfinance_api

    original = naverfinance_api.mobile_json
    naverfinance_api.mobile_json = lambda *args, **kwargs: {
        "isSuccess": False,
        "detailCode": "FE-4000",
        "message": "wrong code.",
        "result": {},
    }
    try:
        try:
            naverfinance_api.front_json("/stock/domestic/basic", {"code": "999999"})
        except RuntimeError as exc:
            assert "FE-4000" in str(exc)
            assert "wrong code" in str(exc)
        else:
            raise AssertionError("front_json should reject Naver error payloads")
    finally:
        naverfinance_api.mobile_json = original


class _FakeResponse:
    def __init__(self, body: bytes = b"{}", content_type: str = "application/json"):
        self._body = body
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._body


def _raise_network_should_not_be_reached(message: str):
    def _mock_urlopen(*args, **kwargs):
        raise AssertionError(message)

    return _mock_urlopen


def test_request_bytes_rejects_non_public_hosts() -> None:
    import naverfinance_api

    original = naverfinance_api.urllib.request.urlopen
    naverfinance_api.urllib.request.urlopen = _raise_network_should_not_be_reached(
        "network should not be reached for blocked hosts"
    )
    try:
        try:
            naverfinance_api.request_bytes("https://example.com/public.json")
        except RuntimeError as exc:
            assert "Unsupported Naver public host" in str(exc)
        else:
            raise AssertionError("non-Naver hosts should be rejected before request")
    finally:
        naverfinance_api.urllib.request.urlopen = original


def test_request_bytes_rejects_sensitive_markers() -> None:
    import naverfinance_api

    original = naverfinance_api.urllib.request.urlopen
    naverfinance_api.urllib.request.urlopen = _raise_network_should_not_be_reached(
        "network should not be reached for sensitive URLs"
    )
    blocked = [
        "https://finance.naver.com/login.naver",
        "https://m.stock.naver.com/front-api/my/holding",
        "https://finance.naver.com/api/order/list",
        "https://api.stock.naver.com/marketindex/exchange/FX_USDKRW/prices?auth_token=secret",
        "https://polling.finance.naver.com/api/realtime?query=SERVICE_MYSTOCK_ITEM:005930",
    ]
    try:
        for url in blocked:
            try:
                naverfinance_api.request_bytes(url)
            except RuntimeError as exc:
                assert "sensitive" in str(exc).lower()
            else:
                raise AssertionError(
                    f"sensitive URL should be rejected before request: {url}"
                )
    finally:
        naverfinance_api.urllib.request.urlopen = original


def test_request_bytes_allows_public_naver_hosts() -> None:
    import naverfinance_api

    original = naverfinance_api.urllib.request.urlopen
    calls = []

    def fake_urlopen(req, timeout=None):
        calls.append(req.full_url)
        return _FakeResponse(b"ok", "text/plain; charset=utf-8")

    naverfinance_api.urllib.request.urlopen = fake_urlopen
    try:
        body, content_type = naverfinance_api.request_bytes(
            "https://finance.naver.com/main/mainSummary.naver?sortOrder=desc"
        )
        assert body == b"ok"
        assert "text/plain" in content_type
        assert calls == [
            "https://finance.naver.com/main/mainSummary.naver?sortOrder=desc"
        ]
    finally:
        naverfinance_api.urllib.request.urlopen = original


def test_skill_description_is_short_and_positive() -> None:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = text.split("---", 2)[1]
    desc = next(
        line.removeprefix("description: ").strip()
        for line in frontmatter.splitlines()
        if line.startswith("description: ")
    )
    assert len(desc) <= 220
    assert "public" in desc
    assert "read-only" in desc
    for broad in ["order", "balance", "holding", "personalized", "WTS", "comment"]:
        assert broad.lower() not in desc.lower()


def test_public_prompts_do_not_depend_on_dollar_selector() -> None:
    for relpath in [
        "README.md",
        "SKILL.md",
        "agents/openai.yaml",
        "references/eval-prompts.md",
    ]:
        text = (ROOT / relpath).read_text(encoding="utf-8")
        assert "$naverfinance-web-api" not in text


def test_codex_install_path_uses_agents_skills() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "$HOME/.agents/skills" in text
    assert ".codex/skills" not in text


def test_release_checklist_covers_public_skill_surface() -> None:
    text = (ROOT / ".github" / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    required = [
        "SKILL.md",
        "$HOME/.agents/skills",
        "$naverfinance-web-api",
        "sensitive",
        "ruff",
        "selftest",
        "unofficial",
    ]
    for marker in required:
        assert marker in text, (
            f"Required marker {marker!r} is missing from RELEASE_CHECKLIST.md"
        )


def test_theme_and_upjong_tables_are_selected() -> None:
    import market_ranking

    theme_fixture = """
    <table class="type_1">
      <tr><th>테마명</th><th>전일대비</th><th>최근3일등락률</th></tr>
      <tr><td>상승</td><td>보합</td><td>하락</td></tr>
      <tr><td>반도체</td><td>+1.20%</td><td>+3.40%</td></tr>
    </table>
    """
    upjong_fixture = """
    <table class="type_1">
      <tr><th>업종명</th><th>전일대비</th><th>등락그래프</th></tr>
      <tr><td>전체</td><td>상승</td><td>하락</td></tr>
      <tr><td>전기전자</td><td>+1.20%</td><td>상승</td></tr>
    </table>
    """
    original_pc_text = market_ranking.pc_text
    original_front_json = market_ranking.front_json
    market_ranking.pc_text = lambda path, *args, **kwargs: (
        upjong_fixture if "sise_group" in path else theme_fixture
    )
    market_ranking.front_json = lambda *args, **kwargs: (_ for _ in ()).throw(
        RuntimeError("skip")
    )
    try:
        theme = market_ranking.fetch_ranking("theme", market="kospi", page=1, limit=5)
        upjong = market_ranking.fetch_ranking("upjong", market="kospi", page=1, limit=5)
        assert theme["rows"] and theme["rows"][0]["테마명"] == "반도체"
        assert upjong["rows"] and upjong["rows"][0]["업종명"] == "전기전자"
    finally:
        market_ranking.pc_text = original_pc_text
        market_ranking.front_json = original_front_json


def test_group_rows_include_detail_links() -> None:
    import market_ranking

    fixture = """
    <table class="type_1">
      <tr><th>그룹명</th><th>전일대비</th></tr>
      <tr><td>전체</td><td>상승</td></tr>
      <tr><td><a href="/sise/sise_group_detail.naver?type=group&no=103">신세계</a></td><td>+4.32%</td></tr>
    </table>
    """
    original_pc_text = market_ranking.pc_text
    original_front_json = market_ranking.front_json
    market_ranking.pc_text = lambda *args, **kwargs: fixture
    market_ranking.front_json = lambda *args, **kwargs: (_ for _ in ()).throw(
        RuntimeError("skip")
    )
    try:
        payload = market_ranking.fetch_ranking("group", market="kospi", page=1, limit=5)
        assert payload["rows"][0]["그룹명"] == "신세계"
        assert payload["rows"][0]["detailNo"] == "103"
        assert (
            payload["rows"][0]["detailUrl"]
            == "/sise/sise_group_detail.naver?type=group&no=103"
        )
    finally:
        market_ranking.pc_text = original_pc_text
        market_ranking.front_json = original_front_json


def test_group_detail_stocks_are_selected() -> None:
    import market_ranking

    fixture = """
    <table class="type_5">
      <tr><th>종목명</th><th>현재가</th><th>전일비</th><th>등락률</th><th>매수호가</th><th>매도호가</th><th>거래량</th><th>거래대금</th><th>전일거래량</th><th>토론</th></tr>
      <tr><td></td></tr>
      <tr><td><a href="/item/main.naver?code=069960">현대백화점</a></td><td>테마 편입 사유 현대백화점 설명</td><td>114,000</td><td>상승 15,500</td><td>+15.74%</td><td>99,300</td><td>99,700</td><td>59,178</td><td>6,558</td><td>87,278</td><td></td></tr>
    </table>
    """
    original_pc_text = market_ranking.pc_text
    market_ranking.pc_text = lambda *args, **kwargs: fixture
    try:
        payload = market_ranking.fetch_group_detail("theme", "318", page=1, limit=5)
        row = payload["rows"][0]
        assert row["종목명"] == "현대백화점"
        assert row["code"] == "069960"
        assert row["편입사유"].startswith("테마 편입 사유")
        assert row["현재가"] == "114,000"
    finally:
        market_ranking.pc_text = original_pc_text


def test_etf_and_etn_api_rows_are_selected() -> None:
    import market_ranking

    def fake_json(url, **kwargs):
        if "etfItemList" in url:
            return {
                "resultCode": "success",
                "result": {
                    "etfItemList": [{"itemcode": "069500", "itemname": "KODEX 200"}]
                },
            }
        return {
            "resultCode": "success",
            "result": {
                "etnItemList": [{"itemcode": "530036", "itemname": "삼성 인버스"}]
            },
        }

    original = market_ranking.request_json_url
    original_front_json = market_ranking.front_json
    market_ranking.request_json_url = fake_json
    market_ranking.front_json = lambda *args, **kwargs: (_ for _ in ()).throw(
        RuntimeError("skip")
    )
    try:
        etf = market_ranking.fetch_ranking("etf", market="kospi", page=1, limit=5)
        etn = market_ranking.fetch_ranking("etn", market="kospi", page=1, limit=5)
        assert etf["rows"][0]["itemcode"] == "069500"
        assert etn["rows"][0]["itemcode"] == "530036"
    finally:
        market_ranking.request_json_url = original
        market_ranking.front_json = original_front_json


def test_konex_api_rows_are_selected() -> None:
    import market_ranking

    original = market_ranking.request_json_url
    market_ranking.request_json_url = lambda *args, **kwargs: {
        "resultCode": "success",
        "result": {"konexItemList": [{"itemcode": "496320", "itemname": "본시스템즈"}]},
    }
    try:
        payload = market_ranking.fetch_ranking("konex", market="kospi", page=1, limit=5)
        assert payload["rows"][0]["itemcode"] == "496320"
    finally:
        market_ranking.request_json_url = original


def test_new_sise_menu_paths_are_mapped() -> None:
    import market_ranking

    fixture = """
    <table class="type_2">
      <tr><th>N</th><th>종목명</th><th>현재가</th></tr>
      <tr><td>1</td><td>삼성전자</td><td>220,000</td></tr>
    </table>
    """
    original = market_ranking.pc_text
    market_ranking.pc_text = lambda *args, **kwargs: fixture
    try:
        for kind in [
            "low-up",
            "high-down",
            "quant-high",
            "quant-low",
            "nxt-market-cap",
            "nxt-volume",
            "nxt-rise",
            "nxt-fall",
            "golden-cross",
            "gap-up",
            "disparity-overheat",
            "sentiment-overheat",
            "relative-strength-overheat",
            "new-stock",
        ]:
            assert market_ranking.fetch_ranking(kind, market="kospi", page=1, limit=1)[
                "rows"
            ]
    finally:
        market_ranking.pc_text = original


def test_popular_search_menu_path_is_mapped() -> None:
    import market_ranking

    fixture = """
    <table class="type_5">
      <tr><th>순위</th><th>종목명</th><th>검색비율</th></tr>
      <tr><td>1</td><td>삼성전자</td><td>12.3%</td></tr>
    </table>
    """
    original = market_ranking.pc_text
    market_ranking.pc_text = lambda *args, **kwargs: fixture
    try:
        assert market_ranking.fetch_ranking(
            "popular-search", market="kospi", page=1, limit=1
        )["rows"]
    finally:
        market_ranking.pc_text = original


def test_investor_program_and_deal_tables_are_selected() -> None:
    import market_ranking

    fixture = """
    <table class="type_1">
      <tr><th>시간</th><th>개인</th><th>외국인</th></tr>
      <tr><td>09:00</td><td>1</td><td>-1</td></tr>
    </table>
    """
    original_pc_text = market_ranking.pc_text
    original_today = market_ranking.today_yyyymmdd
    market_ranking.pc_text = lambda *args, **kwargs: fixture
    market_ranking.today_yyyymmdd = lambda: "20260427"
    try:
        assert market_ranking.fetch_ranking(
            "investor-trend", market="kospi", page=1, limit=1
        )["rows"]
        assert market_ranking.fetch_ranking(
            "program-trend", market="kospi", page=1, limit=1
        )["rows"]
        assert market_ranking.fetch_ranking(
            "foreign-buy", market="kospi", page=1, limit=1
        )["rows"]
        assert market_ranking.fetch_ranking(
            "institution-buy", market="kospi", page=1, limit=1
        )["rows"]
    finally:
        market_ranking.pc_text = original_pc_text
        market_ranking.today_yyyymmdd = original_today


def test_chart_dates_are_validated() -> None:
    import argparse
    import stock_chart

    assert stock_chart.normalize_yyyymmdd("20260427") == "20260427"
    try:
        stock_chart.normalize_yyyymmdd("2026-04-27")
    except argparse.ArgumentTypeError:
        pass
    else:
        raise AssertionError("dates must be accepted only as YYYYMMDD")


def test_market_index_codes_route_to_pc_tables() -> None:
    import indices

    fixture = """
    <table class="tbl_exchange" summary="고시환율 리스트">
      <tr><th>구분</th><th>환율</th></tr>
      <tr><td>현찰 사실때</td><td>1,503.35</td></tr>
    </table>
    """
    original_pc_text = indices.pc_text
    calls = []

    def fake_pc_text(path, params=None, **kwargs):
        calls.append((path, params or {}))
        return fixture

    indices.pc_text = fake_pc_text
    try:
        payload = indices.fetch_index(
            "FX_USDKRW",
            include_chart=False,
            period="day",
            start=None,
            end=None,
            limit=1,
        )
        assert payload["source"] == "finance.naver.com public market-index HTML table"
        assert payload["tables"][0]["rows"][0]["구분"] == "현찰 사실때"
        indices.fetch_index(
            "FX_USDJPY",
            include_chart=False,
            period="day",
            start=None,
            end=None,
            limit=1,
        )
        indices.fetch_index(
            "IRR_CD91", include_chart=False, period="day", start=None, end=None, limit=1
        )
        indices.fetch_index(
            "OIL_GSL", include_chart=False, period="day", start=None, end=None, limit=1
        )
        indices.fetch_index(
            "CMDT_GC", include_chart=False, period="day", start=None, end=None, limit=1
        )
        assert calls[-4][0] == "/marketindex/worldExchangeDetail.naver"
        assert calls[-3][0] == "/marketindex/interestDetail.naver"
        assert calls[-2][0] == "/marketindex/oilDetail.naver"
        assert calls[-1][0] == "/marketindex/worldGoldDetail.naver"
    finally:
        indices.pc_text = original_pc_text


def test_world_hours_rowspan_rows_are_normalized() -> None:
    import world

    fixture = """
    <table cellpadding="0" cellspacing="0">
      <tr><th>대륙</th><th>국가</th><th>현지시간</th><th>한국시간</th><th>GMT 대비</th><th>DST 적용시간</th></tr>
      <tr><th rowspan="2">아시아</th><td>한국</td><td>09:00~15:30</td><td>09:00~15:30</td><td>+9</td><td></td></tr>
      <tr><td>호주</td><td>10:00~16:00</td><td>09:00~15:00</td><td>+10</td><td>08:00~14:00</td></tr>
      <tr><th>미주</th><td>미국</td><td>09:30~16:00</td><td>23:30~06:00</td><td>-5</td><td>22:30~05:00</td></tr>
    </table>
    """
    original = world.pc_text
    world.pc_text = lambda *args, **kwargs: fixture
    try:
        payload = world.fetch_world("hours", symbol=None, page=1, limit=0)
        assert payload["source"] == "finance.naver.com public world trading-hours table"
        assert payload["rows"][0]["대륙"] == "아시아"
        assert payload["rows"][1]["대륙"] == "아시아"
        assert payload["rows"][1]["국가"] == "호주"
        assert payload["rows"][2]["대륙"] == "미주"
        assert payload["rows"][2]["DST 적용시간"] == "22:30~05:00"
    finally:
        world.pc_text = original


def test_stock_trend_mobile_payload_is_selected() -> None:
    import stock_trend

    original = stock_trend.front_json
    stock_trend.front_json = lambda *args, **kwargs: {
        "dealTrendInfos": [{"localDate": "20260427"}]
    }
    try:
        payload = stock_trend.fetch_trend("005930", page=1, limit=1)
        assert payload["rows"][0]["localDate"] == "20260427"
    finally:
        stock_trend.front_json = original


def test_research_relative_detail_links_are_attached() -> None:
    import research

    html = '<a href="company_read.naver?nid=91969&page=1">하반기부터 다시 많아질 이야기거리</a>'
    rows = [{"제목": "하반기부터 다시 많아질 이야기거리"}]
    research._attach_links(rows, html)
    assert rows[0]["detailUrl"] == "/research/company_read.naver?nid=91969&page=1"


def test_news_search_requires_query_and_fetches_rows() -> None:
    import news

    original = news.pc_text
    news.pc_text = lambda *args, **kwargs: (
        '<a href="/news/news_read.naver?article_id=1">삼성전자 기사</a>'
    )
    try:
        payload = news.fetch_news_search("삼성전자", page=1, limit=1)
        assert payload["rows"][0]["title"] == "삼성전자 기사"
    finally:
        news.pc_text = original


def test_home_main_summary_limits_sections() -> None:
    import home

    calls = []
    fixture = {
        "message": {
            "result": {
                "topItems": [[{"code": "005930"}, {"code": "000660"}]],
                "nxtTopItems": [[{"code": "005930"}, {"code": "066570"}]],
                "nxtMarketStatus": {"marketStatus": "OPEN"},
                "todayIndexItemList": [{"cd": "KOSPI"}],
            }
        }
    }
    original = home.request_json_url

    def fake_json(url, **kwargs):
        calls.append(url)
        return fixture

    home.request_json_url = fake_json
    try:
        payload = home.fetch_home_summary(limit=1)
        assert payload["source"] == "finance.naver.com public mainSummary JSON"
        assert payload["summary"]["nxtMarketStatus"]["marketStatus"] == "OPEN"
        assert payload["summary"]["topItems"][0] == [{"code": "005930"}]
        assert payload["summary"]["nxtTopItems"][0] == [{"code": "005930"}]
        assert "callback=" not in calls[0]
    finally:
        home.request_json_url = original


def test_quote_service_index_query_is_supported() -> None:
    import quote

    calls = []
    original = quote.request_json_url

    def fake_json(url, **kwargs):
        calls.append(url)
        return {
            "resultCode": "success",
            "result": {"areas": [{"name": "SERVICE_INDEX", "datas": []}]},
        }

    quote.request_json_url = fake_json
    try:
        payload = quote.fetch_quotes([], index_codes=["KOSPI", "KOSDAQ", "KPI200"])
        assert payload["indexes"] == ["KOSPI", "KOSDAQ", "KPI200"]
        assert "SERVICE_INDEX%3AKOSPI%2CKOSDAQ%2CKPI200" in calls[0]
    finally:
        quote.request_json_url = original


def test_marketindex_api_prices_are_selected() -> None:
    import marketindex

    calls = []
    original = marketindex.request_json_url

    def fake_json(url, **kwargs):
        calls.append(url)
        if "/marketindex/energy/" in url:
            return {"localTradedAt": "2026-05-29", "closePrice": "88.00"}
        return [{"localTradedAt": "2026-05-29", "closePrice": "1,507.10"}]

    marketindex.request_json_url = fake_json
    try:
        payload = marketindex.fetch_marketindex(
            "api-prices", code="FX_USDKRW", page=1, limit=1
        )
        assert payload["source"] == "api.stock.naver.com public marketindex JSON"
        assert payload["code"] == "FX_USDKRW"
        assert payload["apiCode"] == "FX_USDKRW"
        assert payload["rows"][0]["closePrice"] == "1,507.10"
        assert calls[0].endswith(
            "/marketindex/exchange/FX_USDKRW/prices?page=1&pageSize=1"
        )
        oil = marketindex.fetch_marketindex(
            "api-prices", code="OIL_CL", page=1, limit=1
        )
        assert oil["apiGroup"] == "energy"
        assert oil["apiCode"] == "CLcv1"
        assert oil["rows"][0]["closePrice"] == "88.00"
        assert calls[1].endswith("/marketindex/energy/CLcv1/prices?page=1&pageSize=1")
    finally:
        marketindex.request_json_url = original


def test_marketindex_api_routes_fx_energy_and_metals() -> None:
    import marketindex

    assert marketindex._api_marketindex_route("FX_USDJPY") == (
        "exchangeWorld",
        "USDJPY",
    )
    assert marketindex._api_marketindex_route("FX_USDX") == ("exchange", ".DXY")
    assert marketindex._api_marketindex_route("OIL_CL") == ("energy", "CLcv1")
    assert marketindex._api_marketindex_route("OIL_BRT") == ("energy", "LCOcv1")
    assert marketindex._api_marketindex_route("OIL_DU") == ("energy", "DCBc1")
    assert marketindex._api_marketindex_route("OIL_GSL") == ("energy", "OIL_GSL")
    assert marketindex._api_marketindex_route("CMDT_GC") == ("metals", "GCcv1")
    assert marketindex._api_marketindex_route("GOLD_KRX") == ("metals", "M04020000")
    try:
        marketindex._api_marketindex_route("IRR_CD91")
    except SystemExit as exc:
        assert "IRR_*" in str(exc)
    else:
        raise AssertionError(
            "legacy-only interest codes should fail before requesting a guessed URL"
        )


def test_marketindex_rejects_unsafe_api_path_segments() -> None:
    import marketindex

    for code in ["FX_USD/JPY", "FX_USD\\JPY", "FX_..", "FX_USD?JPY"]:
        try:
            marketindex._api_marketindex_route(code)
        except SystemExit as exc:
            assert "format" in str(exc)
        else:
            raise AssertionError(
                f"{code} should not be accepted as a marketindex path segment"
            )


def test_marketindex_api_prices_reject_error_payloads() -> None:
    import marketindex

    original = marketindex.request_json_url
    marketindex.request_json_url = lambda *args, **kwargs: {
        "error": "invalid",
        "message": "wrong code",
    }
    try:
        try:
            marketindex.fetch_marketindex(
                "api-prices", code="FX_USDKRW", page=1, limit=1
            )
        except RuntimeError as exc:
            assert "marketindex prices" in str(exc)
        else:
            raise AssertionError(
                "marketindex error payloads should not be returned as rows"
            )
    finally:
        marketindex.request_json_url = original


def test_world_prices_use_world_day_json() -> None:
    import world

    calls = []
    original = world.request_json_url

    def fake_json(url, **kwargs):
        calls.append(url)
        return [{"symb": "NAS@IXIC", "xymd": "20260529", "clos": 100.0}]

    world.request_json_url = fake_json
    try:
        payload = world.fetch_world("prices", symbol="nasdaq", page=1, limit=1)
        assert payload["source"] == "finance.naver.com public worldDayListJson"
        assert payload["symbol"] == "NAS@IXIC"
        assert payload["rows"][0]["xymd"] == "20260529"
        assert "symbol=NAS%40IXIC" in calls[0]
        assert "fdtc=0" in calls[0]
    finally:
        world.request_json_url = original


def test_dividend_and_etf_use_current_mobile_endpoints() -> None:
    import market_ranking

    calls = []
    original = market_ranking.front_json

    def fake_front_json(path, params=None, **kwargs):
        calls.append((path, params or {}))
        if path == "/domestic/stock/list":
            return {"dividends": [{"itemCode": "005930"}]}
        if path == "/domestic/etf/list":
            return {"result": [{"itemCode": "069500"}]}
        raise AssertionError(f"unexpected path: {path}")

    market_ranking.front_json = fake_front_json
    try:
        dividend = market_ranking.fetch_ranking(
            "dividend", market="kospi", page=1, limit=5
        )
        etf = market_ranking.fetch_ranking("etf", market="kospi", page=1, limit=5)
        assert dividend["market"] == "domestic"
        assert etf["market"] == "domestic"
        assert dividend["rows"][0]["itemCode"] == "005930"
        assert etf["rows"][0]["itemCode"] == "069500"
        assert calls[0] == (
            "/domestic/stock/list",
            {"sortType": "dividend", "category": "rate", "page": 1, "pageSize": 5},
        )
        assert calls[1] == (
            "/domestic/etf/list",
            {"sortTypeCode": "aum", "page": 1, "pageSize": 5},
        )
    finally:
        market_ranking.front_json = original


def test_sector_lists_use_current_mobile_endpoint() -> None:
    import market_ranking

    calls = []
    original = market_ranking.front_json

    def fake_front_json(path, params=None, **kwargs):
        calls.append((path, params or {}))
        return {"sectors": [{"sectorCode": "307", "sectorName": "전자제품"}]}

    market_ranking.front_json = fake_front_json
    try:
        payload = market_ranking.fetch_ranking(
            "upjong", market="kospi", page=1, limit=5
        )
        assert payload["source"] == "m.stock.naver.com public sector JSON"
        assert payload["market"] == "domestic"
        assert payload["rows"][0]["sectorCode"] == "307"
        assert payload["rows"][0]["detailNo"] == "307"
        assert (
            payload["rows"][0]["detailUrl"]
            == "/sise/sise_group_detail.naver?type=upjong&no=307"
        )
        assert calls[0] == (
            "/stock/sectors/all",
            {
                "nationType": "domestic",
                "sectorType": "upjong",
                "sectorSortType": "CHANGE_RATE",
                "businessDayCategory": "daily",
                "page": 1,
                "pageSize": 5,
            },
        )
    finally:
        market_ranking.front_json = original


def test_mobile_ranking_fallbacks_mark_reason() -> None:
    import market_ranking

    fixture = """
    <table class="type_1">
      <tr><th>name</th><th>rate</th></tr>
      <tr><td>sample</td><td>1.0%</td></tr>
    </table>
    """
    original_pc_text = market_ranking.pc_text
    original_front_json = market_ranking.front_json
    market_ranking.pc_text = lambda *args, **kwargs: fixture
    market_ranking.front_json = lambda *args, **kwargs: (_ for _ in ()).throw(
        RuntimeError("mobile down")
    )
    try:
        dividend = market_ranking.fetch_ranking(
            "dividend", market="kosdaq", page=1, limit=5
        )
        theme = market_ranking.fetch_ranking("theme", market="kosdaq", page=1, limit=5)
        assert dividend["market"] == "domestic"
        assert "mobile down" in dividend["fallbackReason"]
        assert theme["market"] == "kosdaq"
        assert "mobile down" in theme["fallbackReason"]
    finally:
        market_ranking.pc_text = original_pc_text
        market_ranking.front_json = original_front_json


def test_mobile_ranking_rejects_unexpected_rows_shape() -> None:
    import market_ranking

    fixture = """
    <table class="type_1">
      <tr><th>N</th><th>name</th></tr>
      <tr><td>1</td><td>sample</td></tr>
    </table>
    """
    original_pc_text = market_ranking.pc_text
    original_front_json = market_ranking.front_json
    market_ranking.pc_text = lambda *args, **kwargs: fixture

    def fake_front_json(path, params=None, **kwargs):
        if path == "/domestic/stock/list":
            return {"dividends": {"bad": True}}
        if path == "/stock/sectors/all":
            return {"sectors": {"bad": True}}
        raise AssertionError(f"unexpected path: {path}")

    market_ranking.front_json = fake_front_json
    try:
        dividend = market_ranking.fetch_ranking(
            "dividend", market="kospi", page=1, limit=5
        )
        upjong = market_ranking.fetch_ranking("upjong", market="kospi", page=1, limit=5)
        assert dividend["source"] == "finance.naver.com public PC HTML table"
        assert "Expected dividend rows list" in dividend["fallbackReason"]
        assert upjong["source"] == "finance.naver.com public PC HTML table"
        assert "Expected upjong rows list" in upjong["fallbackReason"]
    finally:
        market_ranking.pc_text = original_pc_text
        market_ranking.front_json = original_front_json


if __name__ == "__main__":
    raise SystemExit(main())
