#!/usr/bin/env python3
"""Fetch public NaverFinance research menu rows."""

from __future__ import annotations

import argparse
import re

from naverfinance_api import (
    add_limit_argument,
    add_output_argument,
    clean_cell,
    emit_output,
    extract_tables,
    pc_text,
    render_json,
    strip_tags,
    table_to_records,
)


KIND_PATHS = {
    "market-info": "/research/market_info_list.naver",
    "invest": "/research/invest_list.naver",
    "company": "/research/company_list.naver",
    "industry": "/research/industry_list.naver",
    "economy": "/research/economy_list.naver",
    "debenture": "/research/debenture_list.naver",
}


def fetch_research(kind: str, *, page: int, limit: int) -> dict:
    html = pc_text(KIND_PATHS[kind], {"page": page})
    rows = []
    for table in extract_tables(html):
        classes = set((table["attrs"].get("class") or "").split())
        if "type_1" not in classes:
            continue
        records = table_to_records(table["rows"])
        if records and (
            "제목" in records[0] or "종목명" in records[0] or "분류" in records[0]
        ):
            rows = records
            break
    _attach_links(rows, html)
    return {
        "source": "finance.naver.com public research HTML table",
        "kind": kind,
        "page": page,
        "rows": rows[:limit] if limit else rows,
    }


def _attach_links(rows: list[dict[str, str]], html: str) -> None:
    by_title = {}
    for href, body in re.findall(
        r'<a[^>]+href="([^"]*(?:/research/)?[^"/]+_read\.naver[^"]*)"[^>]*>(.*?)</a>',
        html,
        flags=re.S,
    ):
        title = clean_cell(strip_tags(body))
        if title:
            by_title[title] = (
                href
                if href.startswith("/") or href.startswith("http")
                else f"/research/{href}"
            )
    for row in rows:
        title = row.get("제목")
        if title in by_title:
            row["detailUrl"] = by_title[title]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=sorted(KIND_PATHS), default="company")
    parser.add_argument("--page", type=int, default=1)
    add_limit_argument(parser, default=10)
    add_output_argument(parser)
    args = parser.parse_args()
    emit_output(
        render_json(fetch_research(args.kind, page=args.page, limit=args.limit)),
        args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
