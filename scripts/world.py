#!/usr/bin/env python3
"""Fetch public NaverFinance world-market menu data."""

from __future__ import annotations

import argparse
import re

from naverfinance_api import (
    PC_BASE_URL,
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


WORLD_SYMBOLS = {
    "dow": "DJI@DJI",
    "nikkei225": "NII@NI225",
    "ftse100": "LNS@FTSE100",
    "nasdaq": "NAS@IXIC",
    "shanghai": "SHS@000001",
    "cac40": "PAS@CAC40",
    "sp500": "SPI@SPX",
    "hangseng": "HSI@HSI",
    "dax": "XTR@DAX30",
}


def fetch_world(kind: str, *, symbol: str | None, page: int, limit: int) -> dict:
    if kind == "overview":
        html = pc_text("/world/")
        return {
            "source": "finance.naver.com public world page",
            "kind": kind,
            "indices": _extract_links(html, "/world/sise.naver")[:limit]
            if limit
            else _extract_links(html, "/world/sise.naver"),
            "news": _extract_links(html, "/news/news_read.naver")[:limit]
            if limit
            else _extract_links(html, "/news/news_read.naver"),
        }
    if kind == "hours":
        return _fetch_hours(limit=limit)
    resolved = WORLD_SYMBOLS.get(symbol or "", symbol)
    if not resolved:
        raise SystemExit("--symbol is required for --kind index or prices")
    if kind == "prices":
        return _fetch_prices(resolved, page=page, limit=limit)
    return _fetch_tables(
        "/world/sise.naver",
        {"symbol": resolved, "fdtc": 0, "page": page},
        kind=kind,
        page=page,
        limit=limit,
    )


def _fetch_prices(symbol: str, *, page: int, limit: int) -> dict:
    rows = request_json_url(
        PC_BASE_URL
        + build_path(
            "/world/worldDayListJson.naver", {"symbol": symbol, "fdtc": 0, "page": page}
        ),
        referer=PC_BASE_URL + "/world/",
    )
    return {
        "source": "finance.naver.com public worldDayListJson",
        "kind": "prices",
        "symbol": symbol,
        "page": page,
        "rows": rows[:limit] if isinstance(rows, list) and limit else rows,
    }


def _fetch_hours(*, limit: int) -> dict:
    html = pc_text("/world/guide_time_list.naver")
    rows = _extract_trading_hours(html)
    return {
        "source": "finance.naver.com public world trading-hours table",
        "kind": "hours",
        "rows": rows[:limit] if limit else rows,
    }


def _extract_trading_hours(html: str) -> list[dict[str, str]]:
    for table in extract_tables(html):
        rows = table["rows"]
        if not rows or rows[0][:6] != [
            "대륙",
            "국가",
            "현지시간",
            "한국시간",
            "GMT 대비",
            "DST 적용시간",
        ]:
            continue
        records = []
        current_continent = ""
        for row in rows[1:]:
            if len(row) == 6:
                current_continent = row[0]
                values = row
            elif len(row) == 5 and current_continent:
                values = [current_continent] + row
            else:
                continue
            records.append(
                {
                    "대륙": clean_cell(values[0]),
                    "국가": clean_cell(values[1]),
                    "현지시간": clean_cell(values[2]),
                    "한국시간": clean_cell(values[3]),
                    "GMT 대비": clean_cell(values[4]),
                    "DST 적용시간": clean_cell(values[5]),
                }
            )
        return records
    return []


def _fetch_tables(path: str, params: dict, *, kind: str, page: int, limit: int) -> dict:
    html = pc_text(path, params)
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
        "source": "finance.naver.com public world HTML table",
        "kind": kind,
        "page": page,
        "tables": tables[:limit] if limit else tables,
    }


def _extract_links(html: str, contains: str) -> list[dict[str, str]]:
    links = []
    seen = set()
    for href, body in re.findall(
        r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, flags=re.S
    ):
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
    parser.add_argument(
        "--kind", choices=["overview", "index", "prices", "hours"], default="overview"
    )
    parser.add_argument(
        "--symbol", help="World index alias or symbol, e.g. nasdaq or NAS@IXIC"
    )
    parser.add_argument("--page", type=int, default=1)
    add_limit_argument(parser, default=10)
    add_output_argument(parser)
    args = parser.parse_args()
    emit_output(
        render_json(
            fetch_world(args.kind, symbol=args.symbol, page=args.page, limit=args.limit)
        ),
        args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
