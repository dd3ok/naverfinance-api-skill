#!/usr/bin/env python3
"""Fetch public Naver stock investor trend rows."""

from __future__ import annotations

import argparse

from naverfinance_api import (
    add_limit_argument,
    add_output_argument,
    emit_output,
    extract_tables,
    front_json,
    normalize_stock_code,
    pc_text,
    render_json,
    table_to_records,
)


def fetch_trend(code: str, *, page: int, limit: int) -> dict:
    code = normalize_stock_code(code)
    try:
        payload = front_json(
            "/stock/domestic/trend",
            {"code": code},
            referer_path=f"/domestic/stock/{code}/total",
        )
        rows = (
            payload.get("dealTrendInfos", payload)
            if isinstance(payload, dict)
            else payload
        )
        return {
            "source": "m.stock.naver.com public front-api JSON",
            "code": code,
            "page": 1,
            "rows": rows[:limit] if isinstance(rows, list) and limit else rows,
        }
    except Exception:
        html = pc_text("/item/frgn.naver", {"code": code, "page": page})
        rows = []
        for table in extract_tables(html):
            records = table_to_records(table["rows"])
            if records and ("날짜" in records[0] or "일자" in records[0]):
                rows = records
                break
        return {
            "source": "finance.naver.com public investor trend HTML table",
            "code": code,
            "page": page,
            "rows": rows[:limit] if limit else rows,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", required=True, type=normalize_stock_code)
    parser.add_argument("--page", type=int, default=1)
    add_limit_argument(parser, default=20)
    add_output_argument(parser)
    args = parser.parse_args()
    emit_output(
        render_json(fetch_trend(args.code, page=args.page, limit=args.limit)),
        args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
