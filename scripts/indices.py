#!/usr/bin/env python3
"""Fetch public Naver index basic data and optional chart rows."""

from __future__ import annotations

import argparse

from naverfinance_api import (
    add_limit_argument,
    add_output_argument,
    emit_output,
    extract_tables,
    front_json,
    normalize_index_code,
    pc_text,
    render_json,
    table_to_records,
)


DOMESTIC_INDEX_CODES = {"KOSPI", "KOSDAQ", "FUT", "KPI100", "KPI200", "KVALUE"}
DOMESTIC_FX_CODES = {"FX_USDKRW", "FX_JPYKRW", "FX_EURKRW", "FX_CNYKRW"}
WORLD_FX_CODES = {"FX_USDJPY", "FX_EURUSD", "FX_GBPUSD", "FX_USDX"}
WORLD_OIL_CODES = {"OIL_CL", "OIL_BRT", "OIL_DU"}
DOMESTIC_OIL_CODES = {"OIL_GSL", "OIL_LO", "OIL_HO"}
WORLD_GOLD_CODES = {"CMDT_GC"}


def fetch_index(
    code: str,
    *,
    include_chart: bool,
    period: str,
    start: str | None,
    end: str | None,
    limit: int,
) -> dict:
    code = normalize_index_code(code)
    if code not in DOMESTIC_INDEX_CODES:
        if include_chart:
            raise SystemExit(
                "--include-chart is supported only for KOSPI, KOSDAQ, and KPI200"
            )
        return fetch_market_index(code, limit=limit)

    payload = {
        "source": "m.stock.naver.com public index JSON",
        "code": code,
        "basic": front_json(
            "/stock/domestic/basic",
            {"code": code, "endType": "index"},
            referer_path=f"/domestic/index/{code}",
        ),
    }
    if include_chart:
        if not start or not end:
            raise SystemExit("--start and --end are required with --include-chart")
        chart_type = {"day": "candleDay", "week": "candleWeek", "month": "candleMonth"}[
            period
        ]
        chart_payload = front_json(
            "/chart/domestic/stock/end",
            {"code": code, "chartInfoType": "index", "scriptChartType": chart_type},
            referer_path=f"/domestic/index/{code}/chart",
        )
        rows = (
            chart_payload.get("priceInfos", [])
            if isinstance(chart_payload, dict)
            else chart_payload
        )
        rows = [row for row in rows if start <= str(row.get("localDate", "")) <= end]
        payload["chart"] = rows[-limit:] if isinstance(rows, list) and limit else rows
    return payload


def fetch_market_index(code: str, *, limit: int) -> dict:
    if "@" in code:
        html = pc_text("/world/sise.naver", {"symbol": code, "fdtc": 0})
        source = "finance.naver.com public world-index HTML table"
    else:
        route = market_index_route(code)
        if route is None:
            supported = "KOSPI, KOSDAQ, KPI200, FX_*, OIL_*, CMDT_*, IRR_*, GOLD_KRX, or world symbols like NAS@IXIC"
            raise SystemExit(
                f"{code} is not supported by indices.py; use one of: {supported}"
            )
        path, params = route
        html = pc_text(path, params)
        source = "finance.naver.com public market-index HTML table"

    tables = []
    for table in extract_tables(html):
        records = table_to_records(table["rows"])
        if records:
            tables.append(
                {
                    "summary": table["attrs"].get("summary", ""),
                    "class": table["attrs"].get("class", ""),
                    "rows": records[:limit] if limit else records,
                }
            )
    return {
        "source": source,
        "code": code,
        "tables": tables[:limit] if limit else tables,
    }


def market_index_route(code: str) -> tuple[str, dict[str, str]] | None:
    if code in DOMESTIC_FX_CODES:
        return "/marketindex/exchangeDetail.naver", {"marketindexCd": code}
    if code in WORLD_FX_CODES:
        return "/marketindex/worldExchangeDetail.naver", {"marketindexCd": code}
    if code in WORLD_OIL_CODES:
        return "/marketindex/worldOilDetail.naver", {"marketindexCd": code}
    if code in DOMESTIC_OIL_CODES:
        return "/marketindex/oilDetail.naver", {"marketindexCd": code}
    if code in WORLD_GOLD_CODES:
        return "/marketindex/worldGoldDetail.naver", {"marketindexCd": code}
    if code == "GOLD_KRX":
        return "/marketindex/goldDetail.naver", {}
    if code.startswith("CMDT_"):
        return "/marketindex/materialDetail.naver", {"marketindexCd": code}
    if code.startswith("IRR_"):
        return "/marketindex/interestDetail.naver", {"marketindexCd": code}
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", required=True, type=normalize_index_code)
    parser.add_argument("--include-chart", action="store_true")
    parser.add_argument("--period", default="day", choices=["day", "week", "month"])
    parser.add_argument("--start", help="YYYYMMDD")
    parser.add_argument("--end", help="YYYYMMDD")
    add_limit_argument(parser, default=200)
    add_output_argument(parser)
    args = parser.parse_args()
    emit_output(
        render_json(
            fetch_index(
                args.code,
                include_chart=args.include_chart,
                period=args.period,
                start=args.start,
                end=args.end,
                limit=args.limit,
            )
        ),
        args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
