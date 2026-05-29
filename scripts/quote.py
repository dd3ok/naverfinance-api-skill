#!/usr/bin/env python3
"""Fetch public realtime quote polling data from NaverFinance."""

from __future__ import annotations

import argparse

from naverfinance_api import (
    POLLING_BASE_URL,
    add_output_argument,
    build_path,
    emit_output,
    normalize_stock_code,
    render_json,
    request_json_url,
)


def fetch_quotes(codes: list[str], *, index_codes: list[str] | None = None) -> dict:
    normalized = [normalize_stock_code(code) for code in codes]
    normalized_indexes = [_normalize_index_quote_code(code) for code in index_codes or []]
    query_parts = []
    if normalized:
        query_parts.append("SERVICE_ITEM:" + ",".join(normalized))
    if normalized_indexes:
        query_parts.append("SERVICE_INDEX:" + ",".join(normalized_indexes))
    if not query_parts:
        raise SystemExit("At least one --code or --index is required")
    payload = request_json_url(
        POLLING_BASE_URL + build_path("/api/realtime", {"query": "|".join(query_parts)}),
        referer="https://finance.naver.com/",
    )
    return {
        "source": "polling.finance.naver.com public realtime endpoint",
        "codes": normalized,
        "indexes": normalized_indexes,
        "payload": payload,
    }


def _normalize_index_quote_code(code: str) -> str:
    value = code.strip().upper()
    aliases = {"KOSPI200": "KPI200"}
    return aliases.get(value, value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--code",
        action="append",
        default=[],
        type=normalize_stock_code,
        help="Six-digit stock code. Repeat --code to fetch multiple quotes.",
    )
    parser.add_argument(
        "--index",
        action="append",
        default=[],
        help="Index code such as KOSPI, KOSDAQ, KPI200, or KVALUE. Repeat to fetch multiple indexes.",
    )
    add_output_argument(parser)
    args = parser.parse_args()
    emit_output(render_json(fetch_quotes(args.code, index_codes=args.index)), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
