#!/usr/bin/env python3
"""Fetch public Wisereport company-analysis data linked from NaverFinance."""

from __future__ import annotations

import argparse
import re

from naverfinance_api import (
    add_limit_argument,
    add_output_argument,
    clean_cell,
    emit_output,
    extract_tables,
    normalize_stock_code,
    render_json,
    strip_tags,
    table_to_records,
    wisereport_text,
)


KIND_PATHS = {
    "overview": "/company/c1010001.aspx",
    "company": "/company/c1020001.aspx",
    "financial-analysis": "/company/c1030001.aspx",
    "indicators": "/company/c1040001.aspx",
    "consensus": "/company/c1050001.aspx",
    "industry": "/company/c1060001.aspx",
    "shareholders": "/company/c1070001.aspx",
    "sector": "/company/c1090001.aspx",
}


def fetch_financials(code: str, *, kind: str, limit: int) -> dict:
    code = normalize_stock_code(code)
    markup = wisereport_text(KIND_PATHS[kind], {"cmp_cd": code})
    bullets = [
        clean_cell(strip_tags(match))
        for match in re.findall(
            r"(?is)<li[^>]+class=['\"][^'\"]*dot_cmp[^'\"]*['\"][^>]*>(.*?)</li>",
            markup,
        )
    ]
    tables = []
    for table in extract_tables(markup):
        records = table_to_records(table["rows"])
        if records:
            tables.append(records[:limit] if limit else records)
    return {
        "source": "navercomp.wisereport.co.kr public company-analysis iframe",
        "code": code,
        "kind": kind,
        "summaryBullets": bullets,
        "tables": tables[:limit] if limit else tables,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", required=True, type=normalize_stock_code)
    parser.add_argument("--kind", choices=sorted(KIND_PATHS), default="overview")
    add_limit_argument(parser, default=5)
    add_output_argument(parser)
    args = parser.parse_args()
    emit_output(
        render_json(fetch_financials(args.code, kind=args.kind, limit=args.limit)),
        args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
