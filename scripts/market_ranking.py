#!/usr/bin/env python3
"""Fetch public NaverFinance domestic market ranking/list tables."""

from __future__ import annotations

import argparse
import re
from datetime import datetime

from naverfinance_api import (
    PC_BASE_URL,
    add_limit_argument,
    add_output_argument,
    build_path,
    clean_cell,
    emit_output,
    extract_tables,
    front_json,
    pc_text,
    render_json,
    request_json_url,
    strip_tags,
    table_to_records,
)


KIND_PATHS = {
    "konex": "/sise/konex.naver",
    "market-cap": "/sise/sise_market_sum.naver",
    "volume": "/sise/sise_quant.naver",
    "quant-high": "/sise/sise_quant_high.naver",
    "quant-low": "/sise/sise_quant_low.naver",
    "rise": "/sise/sise_rise.naver",
    "fall": "/sise/sise_fall.naver",
    "steady": "/sise/sise_steady.naver",
    "upper": "/sise/sise_upper.naver",
    "lower": "/sise/sise_lower.naver",
    "low-up": "/sise/sise_low_up.naver",
    "high-down": "/sise/sise_high_down.naver",
    "etf": "/sise/etf.naver",
    "etn": "/sise/etn.naver",
    "dividend": "/sise/dividend_list.naver",
    "foreign-hold": "/sise/sise_foreign_hold.naver",
    "theme": "/sise/theme.naver",
    "upjong": "/sise/sise_group.naver",
    "group": "/sise/sise_group.naver",
    "investor-trend": "/sise/sise_trans_style.naver",
    "foreign-buy": "/sise/sise_deal_rank.naver",
    "foreign-sell": "/sise/sise_deal_rank.naver",
    "institution-buy": "/sise/sise_deal_rank.naver",
    "institution-sell": "/sise/sise_deal_rank.naver",
    "program-trend": "/sise/sise_program.naver",
    "deposit": "/sise/sise_deposit.naver",
    "new-stock": "/sise/sise_new_stock.naver",
    "market3": "/sise/market3news_list.naver",
    "ipo": "/sise/ipo.naver",
    "nxt-market-cap": "/sise/nxt_sise_market_sum.naver",
    "nxt-volume": "/sise/nxt_sise_quant.naver",
    "nxt-rise": "/sise/nxt_sise_rise.naver",
    "nxt-fall": "/sise/nxt_sise_fall.naver",
    "management": "/sise/management.naver",
    "trading-halt": "/sise/trading_halt.naver",
    "investment-alert": "/sise/investment_alert.naver",
    "popular-search": "/sise/lastsearch2.naver",
    "golden-cross": "/sise/item_gold.naver",
    "gap-up": "/sise/item_gap.naver",
    "disparity-overheat": "/sise/item_igyuk.naver",
    "sentiment-overheat": "/sise/item_overheating_1.naver",
    "relative-strength-overheat": "/sise/item_overheating_2.naver",
    "report": "/sise/report.naver",
    "short-trade": "/sise/short_trade.naver",
}

MARKETS = {"kospi": "0", "kosdaq": "1"}
FRONT_MARKETS = {"kospi": "KOSPI", "kosdaq": "KOSDAQ"}
FRONT_SORT_TYPES = {
    "market-cap": "marketValue",
    "volume": "quantTop",
    "rise": "up",
    "fall": "down",
    "etf": "etf",
    "etn": "etn",
    "dividend": "dividend",
    "management": "management",
}


def _fallback_reason(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"


def fetch_ranking(kind: str, *, market: str, page: int, limit: int) -> dict:
    fallback_reason = None
    if kind == "dividend":
        return fetch_dividend(page=page, limit=limit)
    if kind == "etf":
        return fetch_etf(page=page, limit=limit)
    if kind in {"konex", "etn"}:
        return fetch_exchange_traded_products(kind, page=page, limit=limit)
    if kind in {"theme", "upjong", "group"}:
        try:
            return fetch_sector_list(kind, page=page, limit=limit)
        except Exception as exc:
            fallback_reason = _fallback_reason(exc)
    if kind == "investor-trend":
        return fetch_investor_trend(market=market, page=page, limit=limit)
    if kind == "program-trend":
        return fetch_program_trend(market=market, page=page, limit=limit)
    if kind in {"foreign-buy", "foreign-sell", "institution-buy", "institution-sell"}:
        return fetch_deal_rank(kind, market=market, page=page, limit=limit)
    if kind in {"report", "short-trade"}:
        return fetch_link_only_menu(kind)

    if kind in FRONT_SORT_TYPES:
        try:
            payload = front_json(
                "/stock/domestic/stockList",
                {
                    "sortType": FRONT_SORT_TYPES[kind],
                    "category": FRONT_MARKETS[market],
                    "page": page,
                    "pageSize": limit or 20,
                },
            )
            return {
                "source": "m.stock.naver.com public front-api JSON",
                "kind": kind,
                "market": market,
                "page": page,
                "rows": payload.get("stocks", []) if isinstance(payload, dict) else payload,
            }
        except Exception as exc:
            fallback_reason = _fallback_reason(exc)

    path = KIND_PATHS[kind]
    params: dict[str, str | int] = {"page": page}
    if kind in {"market-cap", "volume", "rise", "fall", "steady", "quant-high", "quant-low"}:
        params["sosok"] = MARKETS[market]
    if kind == "market-cap":
        params["fieldIds"] = "market_sum"
    if kind == "upjong":
        params["type"] = "upjong"
    if kind == "group":
        params["type"] = "group"
    if kind == "investment-alert":
        params["type"] = "caution"
    html = pc_text(path, params)
    rows = _extract_menu_rows(kind, html)
    _attach_detail_links(kind, rows, html)
    result = {
        "source": "finance.naver.com public PC HTML table",
        "kind": kind,
        "market": market,
        "page": page,
        "rows": rows[:limit] if limit else rows,
    }
    if fallback_reason:
        result["fallbackReason"] = fallback_reason
    return result


def fetch_group_detail(kind: str, no: str, *, page: int, limit: int) -> dict:
    if kind not in {"theme", "upjong", "group"}:
        raise SystemExit("--detail-no is supported only for theme, upjong, and group")
    if not no.isdigit():
        raise SystemExit("--detail-no must be numeric")
    html = pc_text("/sise/sise_group_detail.naver", {"type": kind, "no": no, "page": page})
    code_by_name = _extract_stock_code_links(html)
    rows = []
    for table in extract_tables(html):
        classes = set((table["attrs"].get("class") or "").split())
        if "type_5" not in classes:
            continue
        rows = _records_from_detail_rows(table["rows"], code_by_name)
        break
    return {
        "source": "finance.naver.com public group/theme detail HTML table",
        "kind": kind,
        "detailNo": no,
        "page": page,
        "rows": rows[:limit] if limit else rows,
    }


def fetch_exchange_traded_products(kind: str, *, page: int, limit: int) -> dict:
    if kind == "konex":
        payload = request_json_url(
            PC_BASE_URL
            + build_path(
                "/api/sise/konexItemList.nhn",
                {"targetColumn": "market_sum", "sortOrder": "desc"},
            ),
            referer=PC_BASE_URL + "/sise/konex.naver",
        )
        rows = payload.get("result", {}).get("konexItemList", [])
    elif kind == "etf":
        payload = request_json_url(
            PC_BASE_URL
            + build_path(
                "/api/sise/etfItemList.nhn",
                {"etfType": 0, "targetColumn": "market_sum", "sortOrder": "desc"},
            ),
            referer=PC_BASE_URL + "/sise/etf.naver",
        )
        rows = payload.get("result", {}).get("etfItemList", [])
    else:
        payload = request_json_url(
            PC_BASE_URL
            + build_path(
                "/api/sise/etnItemList.nhn",
                {"targetColumn": "acc_quant", "sortOrder": "desc"},
            ),
            referer=PC_BASE_URL + "/sise/etn.naver",
        )
        rows = payload.get("result", {}).get("etnItemList", [])
    if payload.get("resultCode") != "success":
        raise RuntimeError(f"Naver {kind.upper()} API failed: {payload}")
    paged_rows = _local_page(rows, page=page, limit=limit)
    return {
        "source": f"finance.naver.com public {kind.upper()} JSON endpoint",
        "kind": kind,
        "market": "kospi",
        "page": page,
        "rows": paged_rows,
    }


def fetch_dividend(*, page: int, limit: int) -> dict:
    try:
        payload = front_json(
            "/domestic/stock/list",
            {
                "sortType": "dividend",
                "category": "rate",
                "page": page,
                "pageSize": limit or 20,
            },
            referer_path="/domestic/home/dividend/revenue",
        )
        rows = payload.get("dividends", payload.get("stocks", payload)) if isinstance(payload, dict) else payload
        return {
            "source": "m.stock.naver.com public front-api JSON",
            "kind": "dividend",
            "market": "domestic",
            "page": page,
            "rows": rows[:limit] if isinstance(rows, list) and limit else rows,
        }
    except Exception as exc:
        html = pc_text(KIND_PATHS["dividend"], {"page": page})
        rows = _extract_menu_rows("dividend", html)
        return {
            "source": "finance.naver.com public PC HTML table",
            "kind": "dividend",
            "market": "domestic",
            "page": page,
            "rows": rows[:limit] if limit else rows,
            "fallbackReason": _fallback_reason(exc),
        }


def fetch_etf(*, page: int, limit: int) -> dict:
    try:
        payload = front_json(
            "/domestic/etf/list",
            {"sortTypeCode": "aum", "page": page, "pageSize": limit or 20},
            referer_path="/domestic/home/etf/aum",
        )
        rows = payload.get("etfs", payload.get("stocks", payload.get("result", payload))) if isinstance(payload, dict) else payload
        return {
            "source": "m.stock.naver.com public front-api JSON",
            "kind": "etf",
            "market": "domestic",
            "page": page,
            "rows": rows[:limit] if isinstance(rows, list) and limit else rows,
        }
    except Exception as exc:
        result = fetch_exchange_traded_products("etf", page=page, limit=limit)
        result["market"] = "domestic"
        result["fallbackReason"] = _fallback_reason(exc)
        return result


def fetch_sector_list(kind: str, *, page: int, limit: int) -> dict:
    payload = front_json(
        "/stock/sectors/all",
        {
            "nationType": "domestic",
            "sectorType": kind,
            "sectorSortType": "CHANGE_RATE",
            "businessDayCategory": "daily",
            "page": page,
            "pageSize": limit or 20,
        },
        referer_path=f"/domestic/home/{kind}/daily",
    )
    rows = payload.get("sectors", payload.get("result", payload)) if isinstance(payload, dict) else payload
    rows = _with_sector_detail_links(kind, rows)
    return {
        "source": "m.stock.naver.com public sector JSON",
        "kind": kind,
        "market": "domestic",
        "page": page,
        "rows": rows[:limit] if isinstance(rows, list) and limit else rows,
    }


def _with_sector_detail_links(kind: str, rows):
    if not isinstance(rows, list):
        return rows
    for row in rows:
        if not isinstance(row, dict):
            continue
        detail_no = str(row.get("sectorCode") or "")
        if not detail_no:
            continue
        row.setdefault("detailNo", detail_no)
        row.setdefault("detailUrl", build_path("/sise/sise_group_detail.naver", {"type": kind, "no": detail_no}))
    return rows


def fetch_investor_trend(*, market: str, page: int, limit: int) -> dict:
    sosok = "01" if market == "kospi" else "02"
    return _fetch_iframe_table(
        "investor-trend",
        "/sise/investorDealTrendDay.naver",
        {"bizdate": today_yyyymmdd(), "sosok": sosok, "page": page},
        limit=limit,
    )


def fetch_program_trend(*, market: str, page: int, limit: int) -> dict:
    sosok = "01" if market == "kospi" else "02"
    return _fetch_iframe_table(
        "program-trend",
        "/sise/programDealTrendDay.naver",
        {"bizdate": today_yyyymmdd(), "sosok": sosok, "page": page},
        limit=limit,
    )


def fetch_deal_rank(kind: str, *, market: str, page: int, limit: int) -> dict:
    sosok = "01" if market == "kospi" else "02"
    investor = "9000" if kind.startswith("foreign") else "1000"
    trade_type = "sell" if kind.endswith("sell") else "buy"
    return _fetch_iframe_table(
        kind,
        "/sise/sise_deal_rank_iframe.naver",
        {"sosok": sosok, "investor_gubun": investor, "type": trade_type, "page": page},
        limit=limit,
    )


def fetch_link_only_menu(kind: str) -> dict:
    html = pc_text(KIND_PATHS[kind])
    if kind == "short-trade":
        iframes = re.findall(r'<iframe[^>]+src="([^"]+)"', html)
        return {
            "source": "finance.naver.com public short-trade page",
            "kind": kind,
            "rows": [],
            "externalIframes": iframes,
            "note": "Naver embeds KRX short-selling statistics in an iframe; use the iframe URL for current detail data.",
        }
    links = []
    for href, body in re.findall(r'<a[^>]+href="([^"]*report\.naver[^"]*)"[^>]*>(.*?)</a>', html, flags=re.S):
        text = clean_cell(strip_tags(body))
        if text:
            links.append({"label": text, "url": href})
    return {
        "source": "finance.naver.com public disclosure report page",
        "kind": kind,
        "rows": [],
        "links": links,
        "note": "Naver report menu exposes disclosure tabs; detailed disclosure lists may require tab-specific page inspection.",
    }


def _matches_kind_table(kind: str, first_record: dict[str, str]) -> bool:
    keys = set(first_record)
    if kind == "theme":
        return any("테마명" in key for key in keys)
    if kind == "upjong":
        return any("업종명" in key for key in keys)
    if kind == "group":
        return any("그룹명" in key for key in keys)
    return any("종목" in key or "종목명" in key for key in keys)


def _extract_menu_rows(kind: str, html: str) -> list[dict[str, str]]:
    for table in extract_tables(html):
        attrs = table["attrs"]
        classes = set((attrs.get("class") or "").split())
        if classes.intersection({"item_list", "type_r1", "Nnavi"}):
            continue
        if not classes.intersection({"type_1", "type_2", "type_5", "type_7", "table_kos_index"}):
            continue
        records = table_to_records(table["rows"])
        if not records:
            continue
        if _matches_kind_table(kind, records[0]) or _is_generic_menu_table(records[0]):
            return _clean_kind_records(kind, records)
    return []


def _is_generic_menu_table(first_record: dict[str, str]) -> bool:
    keys = set(first_record)
    return bool(
        keys.intersection(
            {
                "N",
                "날짜",
                "종목",
                "투자정보",
                "구분",
                "시간",
                "거래량",
                "현재가",
                "등락률",
            }
        )
    )


def _clean_kind_records(kind: str, records: list[dict[str, str]]) -> list[dict[str, str]]:
    if kind in {"deposit", "investor-trend", "program-trend"}:
        return _drop_header_like_rows(records)
    if kind not in {"theme", "upjong", "group"}:
        return records
    name_key = {"theme": "테마명", "upjong": "업종명", "group": "그룹명"}[kind]
    header_labels = {"상승", "보합", "하락", "전체"}
    cleaned = []
    for record in records:
        if record.get(name_key) in header_labels and not _has_numeric_change(record):
            continue
        cleaned.append(record)
    return cleaned


def _drop_header_like_rows(records: list[dict[str, str]]) -> list[dict[str, str]]:
    cleaned = []
    for record in records:
        first_value = next(iter(record.values()), "")
        if first_value and not re.search(r"\d", first_value):
            continue
        cleaned.append(record)
    return cleaned


def _has_numeric_change(record: dict[str, str]) -> bool:
    return any("%" in value or value.startswith(("+", "-")) for value in record.values())


def _fetch_iframe_table(kind: str, path: str, params: dict[str, str | int], *, limit: int) -> dict:
    html = pc_text(path, params)
    rows = _extract_menu_rows(kind, html)
    return {
        "source": "finance.naver.com public PC iframe table",
        "kind": kind,
        "params": params,
        "rows": rows[:limit] if limit else rows,
    }


def today_yyyymmdd() -> str:
    return datetime.now().strftime("%Y%m%d")


def _attach_detail_links(kind: str, rows: list[dict[str, str]], html: str) -> None:
    if kind not in {"theme", "upjong", "group"}:
        return
    name_key = {"theme": "테마명", "upjong": "업종명", "group": "그룹명"}[kind]
    links = _extract_group_detail_links(html, kind)
    for row in rows:
        link = links.get(row.get(name_key, ""))
        if not link:
            continue
        row["detailNo"] = link["no"]
        row["detailUrl"] = link["url"]


def _extract_group_detail_links(html: str, kind: str) -> dict[str, dict[str, str]]:
    links = {}
    pattern = rf'<a[^>]+href="([^"]*sise_group_detail\.naver\?type={kind}&no=(\d+)[^"]*)"[^>]*>(.*?)</a>'
    for url, no, body in re.findall(pattern, html, flags=re.S):
        name = clean_cell(strip_tags(body))
        links[name] = {"no": no, "url": url}
    return links


def _extract_stock_code_links(html: str) -> dict[str, dict[str, str]]:
    links = {}
    pattern = r'<a[^>]+href="([^"]*/item/main\.naver\?code=(\d{6})[^"]*)"[^>]*>(.*?)</a>'
    for url, code, body in re.findall(pattern, html, flags=re.S):
        name = clean_cell(strip_tags(body))
        links[name] = {"code": code, "itemUrl": url}
    return links


def _records_from_detail_rows(rows: list[list[str]], code_by_name: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    header = next((row for row in rows if row and row[0] == "종목명"), [])
    if not header:
        return []
    records = []
    for row in rows[rows.index(header) + 1 :]:
        if len(row) < len(header) or not row[0].strip():
            continue
        if len(row) == len(header) + 1:
            keys = [header[0], "편입사유", *header[1:]]
        else:
            keys = header
        record = {keys[idx]: clean_cell(value) for idx, value in enumerate(row[: len(keys)])}
        link = code_by_name.get(record.get("종목명", ""))
        if link:
            record.update(link)
        records.append(record)
    return records


def _local_page(rows: list[dict], *, page: int, limit: int) -> list[dict]:
    if not limit:
        return rows
    start = max(page - 1, 0) * limit
    return rows[start : start + limit]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=sorted(KIND_PATHS), default="market-cap")
    parser.add_argument("--market", choices=sorted(MARKETS), default="kospi")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--detail-no", help="Fetch stocks for a theme/upjong/group detail number")
    add_limit_argument(parser, default=20)
    add_output_argument(parser)
    args = parser.parse_args()
    if args.detail_no:
        payload = fetch_group_detail(args.kind, args.detail_no, page=args.page, limit=args.limit)
    else:
        payload = fetch_ranking(args.kind, market=args.market, page=args.page, limit=args.limit)
    emit_output(render_json(payload), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
