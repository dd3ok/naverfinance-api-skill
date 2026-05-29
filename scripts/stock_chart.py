#!/usr/bin/env python3
"""Fetch public Naver stock chart rows."""

from __future__ import annotations

import argparse
import ast
import re

from naverfinance_api import (
    LEGACY_API_BASE_URL,
    add_limit_argument,
    add_output_argument,
    build_path,
    emit_output,
    front_json,
    normalize_stock_code,
    render_json,
    request_text,
)


def normalize_yyyymmdd(value: str) -> str:
    if not re.fullmatch(r"\d{8}", value):
        raise argparse.ArgumentTypeError("date must be YYYYMMDD")
    return value


def fetch_chart(
    code: str,
    *,
    period: str,
    start: str,
    end: str,
    limit: int,
    fallback_legacy: bool,
) -> dict:
    code = normalize_stock_code(code)
    chart_type = {"day": "candleDay", "week": "candleWeek", "month": "candleMonth"}[
        period
    ]
    try:
        payload = front_json(
            "/chart/domestic/stock/end",
            {"code": code, "chartInfoType": "item", "scriptChartType": chart_type},
            referer_path=f"/domestic/stock/{code}/chart",
        )
        rows = payload.get("priceInfos", []) if isinstance(payload, dict) else payload
        rows = [row for row in rows if start <= str(row.get("localDate", "")) <= end]
        if isinstance(rows, list):
            return {
                "source": "m.stock.naver.com public chart JSON",
                "code": code,
                "period": period,
                "rows": rows[-limit:] if limit else rows,
            }
    except Exception:
        if not fallback_legacy:
            raise

    text = request_text(
        LEGACY_API_BASE_URL
        + build_path(
            "/siseJson.naver",
            {
                "symbol": code,
                "requestType": 1,
                "startTime": start,
                "endTime": end,
                "timeframe": period,
            },
        ),
        referer="https://finance.naver.com/",
    )
    cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    rows = ast.literal_eval(cleaned)
    header = rows[0]
    records = [dict(zip(header, row)) for row in rows[1:]]
    return {
        "source": "api.finance.naver.com legacy siseJson",
        "code": code,
        "period": period,
        "rows": records[-limit:] if limit else records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", required=True, type=normalize_stock_code)
    parser.add_argument("--period", default="day", choices=["day", "week", "month"])
    parser.add_argument(
        "--start", required=True, type=normalize_yyyymmdd, help="YYYYMMDD"
    )
    parser.add_argument(
        "--end", required=True, type=normalize_yyyymmdd, help="YYYYMMDD"
    )
    parser.add_argument("--no-fallback-legacy", action="store_true")
    add_limit_argument(parser, default=200)
    add_output_argument(parser)
    args = parser.parse_args()
    payload = fetch_chart(
        args.code,
        period=args.period,
        start=args.start,
        end=args.end,
        limit=args.limit,
        fallback_legacy=not args.no_fallback_legacy,
    )
    emit_output(render_json(payload), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
