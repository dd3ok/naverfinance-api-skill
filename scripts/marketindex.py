#!/usr/bin/env python3
"""Fetch public NaverFinance market-index menu data."""

from __future__ import annotations

import argparse
import re

from indices import fetch_market_index
from naverfinance_api import (
    STOCK_API_BASE_URL,
    add_limit_argument,
    add_output_argument,
    build_path,
    clean_cell,
    emit_output,
    extract_tables,
    pc_text,
    render_json,
    request_json_url,
    strip_tags,
    table_to_records,
)


API_MARKETINDEX_ALIASES = {
    "DXY": ("exchange", ".DXY"),
    "FX_USDX": ("exchange", ".DXY"),
    "OIL_CL": ("energy", "CLcv1"),
    "OIL_BRT": ("energy", "LCOcv1"),
    "OIL_DU": ("energy", "DCBc1"),
    "OIL_DUBAI": ("energy", "DCBc1"),
    "OIL_GSL": ("energy", "OIL_GSL"),
    "OIL_HGSL": ("energy", "OIL_HGSL"),
    "OIL_LO": ("energy", "OIL_LO"),
    "CMDT_GC": ("metals", "GCcv1"),
    "GOLD_KRX": ("metals", "M04020000"),
    "CMDT_SI": ("metals", "SIcv1"),
    "CMDT_HG": ("metals", "HGcv1"),
    "CMDT_PL": ("metals", "PLcv1"),
    "CMDT_PA": ("metals", "PAcv1"),
    "CMDT_TIO": ("metals", "TIOc1"),
    "METAL_CU": ("metals", "CMCU0"),
    "METAL_AA": ("metals", "CMAA0"),
    "METAL_PB": ("metals", "CMPB0"),
    "METAL_ZN": ("metals", "CMZN0"),
    "METAL_NI": ("metals", "CMNI0"),
    "METAL_SN": ("metals", "CMSN0"),
    "CLCV1": ("energy", "CLcv1"),
    "LCOCV1": ("energy", "LCOcv1"),
    "RBCV1": ("energy", "RBcv1"),
    "HOCV1": ("energy", "HOcv1"),
    "DCBC1": ("energy", "DCBc1"),
    "NGCV1": ("energy", "NGcv1"),
    "GCCV1": ("metals", "GCcv1"),
    "SICV1": ("metals", "SIcv1"),
    "HGCV1": ("metals", "HGcv1"),
    "PLCV1": ("metals", "PLcv1"),
    "PACV1": ("metals", "PAcv1"),
    "TIOC1": ("metals", "TIOc1"),
    "M04020000": ("metals", "M04020000"),
}
API_CODE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def fetch_marketindex(kind: str, *, code: str | None, page: int, limit: int) -> dict:
    if kind == "overview":
        html = pc_text("/marketindex/")
        return {
            "source": "finance.naver.com public marketindex page",
            "kind": kind,
            "marketIndexes": _extract_links(html, "/marketindex/")[:limit] if limit else _extract_links(html, "/marketindex/"),
            "news": _extract_links(html, "/news/news_read.naver")[:limit] if limit else _extract_links(html, "/news/news_read.naver"),
            "research": _extract_links(html, "/research/")[:limit] if limit else _extract_links(html, "/research/"),
        }
    if kind == "exchange-list":
        return _fetch_tables("/marketindex/exchangeList.naver", {}, kind=kind, page=page, limit=limit)
    if kind == "api-prices":
        if not code:
            raise SystemExit("--code is required for --kind api-prices")
        return fetch_api_prices(code, page=page, limit=limit)
    if kind == "api-detail":
        if not code:
            raise SystemExit("--code is required for --kind api-detail")
        return fetch_api_detail(code)
    if not code:
        raise SystemExit("--code is required for --kind detail")
    return fetch_market_index(code, limit=limit)


def fetch_api_prices(code: str, *, page: int, limit: int) -> dict:
    group, api_code = _api_marketindex_route(code)
    payload = request_json_url(
        STOCK_API_BASE_URL
        + build_path(f"/marketindex/{group}/{api_code}/prices", {"page": page, "pageSize": limit or 10}),
        referer="https://m.stock.naver.com/",
    )
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("prices")
        if rows is None:
            rows = [payload]
    else:
        raise RuntimeError(f"Unexpected marketindex prices payload for {code}: {payload!r}")
    return {
        "source": "api.stock.naver.com public marketindex JSON",
        "kind": "api-prices",
        "code": code,
        "apiGroup": group,
        "apiCode": api_code,
        "page": page,
        "rows": rows[:limit] if isinstance(rows, list) and limit else rows,
    }


def fetch_api_detail(code: str) -> dict:
    group, api_code = _api_marketindex_route(code)
    payload = request_json_url(
        STOCK_API_BASE_URL + f"/marketindex/{group}/{api_code}",
        referer="https://m.stock.naver.com/",
    )
    return {
        "source": "api.stock.naver.com public marketindex JSON",
        "kind": "api-detail",
        "code": code,
        "apiGroup": group,
        "apiCode": api_code,
        "payload": payload,
    }


def _api_marketindex_route(code: str) -> tuple[str, str]:
    value = code.strip().upper()
    if value in API_MARKETINDEX_ALIASES:
        group, api_code = API_MARKETINDEX_ALIASES[value]
        return group, _api_code_segment(api_code)
    if value.startswith("FX_"):
        tail = _api_code_segment(value[3:])
        if tail.endswith("KRW"):
            return "exchange", _api_code_segment(value)
        return "exchangeWorld", tail
    raise SystemExit(
        "--kind api-detail/api-prices supports FX_* exchange codes, FX_USDX, energy, and metals codes; "
        "use --kind detail for legacy-only marketindex pages such as IRR_* interest rates"
    )


def _api_code_segment(value: str) -> str:
    if not API_CODE_SEGMENT_RE.fullmatch(value) or ".." in value:
        raise SystemExit("Unsupported marketindex code format")
    return value


def _fetch_tables(path: str, params: dict, *, kind: str, page: int, limit: int) -> dict:
    html = pc_text(path, params)
    tables = []
    for table in extract_tables(html):
        records = _clean_records(table_to_records(table["rows"]))
        if records:
            tables.append(
                {
                    "summary": table["attrs"].get("summary", ""),
                    "class": table["attrs"].get("class", ""),
                    "rows": records[:limit] if limit else records,
                }
            )
    return {"source": "finance.naver.com public marketindex HTML table", "kind": kind, "page": page, "tables": tables[:limit] if limit else tables}


def _clean_records(records: list[dict[str, str]]) -> list[dict[str, str]]:
    return [record for record in records if any(re.search(r"\d", value) for value in record.values())]


def _extract_links(html: str, contains: str) -> list[dict[str, str]]:
    links = []
    seen = set()
    for href, body in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, flags=re.S):
        if contains not in href:
            continue
        label = clean_cell(strip_tags(body))
        if not label or (label, href) in seen:
            continue
        seen.add((label, href))
        links.append({"label": label, "url": href})
    return links


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=["overview", "exchange-list", "detail", "api-detail", "api-prices"], default="overview")
    parser.add_argument("--code", help="Market index code, e.g. FX_USDKRW, FX_USDJPY, FX_USDX, OIL_CL, CMDT_GC, IRR_CD91")
    parser.add_argument("--page", type=int, default=1)
    add_limit_argument(parser, default=10)
    add_output_argument(parser)
    args = parser.parse_args()
    emit_output(render_json(fetch_marketindex(args.kind, code=args.code, page=args.page, limit=args.limit)), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
