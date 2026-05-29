#!/usr/bin/env python3
"""Fetch public NaverFinance stock news or disclosure tables."""

from __future__ import annotations

import argparse
import re

from naverfinance_api import (
    add_limit_argument,
    add_output_argument,
    emit_output,
    extract_tables,
    front_json,
    normalize_stock_code,
    pc_text,
    render_json,
    strip_tags,
    clean_cell,
    table_to_records,
)


NEWS_KIND_PARAMS = {
    "flash": (
        "/news/news_list.naver",
        {"mode": "LSS2D", "section_id": "101", "section_id2": "258"},
    ),
    "main": ("/news/mainnews.naver", {}),
    "market": (
        "/news/news_list.naver",
        {
            "mode": "LSS3D",
            "section_id": "101",
            "section_id2": "258",
            "section_id3": "401",
        },
    ),
    "analysis": (
        "/news/news_list.naver",
        {
            "mode": "LSS3D",
            "section_id": "101",
            "section_id2": "258",
            "section_id3": "402",
        },
    ),
    "world": (
        "/news/news_list.naver",
        {
            "mode": "LSS3D",
            "section_id": "101",
            "section_id2": "258",
            "section_id3": "403",
        },
    ),
    "bond": (
        "/news/news_list.naver",
        {
            "mode": "LSS3D",
            "section_id": "101",
            "section_id2": "258",
            "section_id3": "404",
        },
    ),
    "memo": (
        "/news/news_list.naver",
        {
            "mode": "LSS3D",
            "section_id": "101",
            "section_id2": "258",
            "section_id3": "406",
        },
    ),
    "fx": (
        "/news/news_list.naver",
        {
            "mode": "LSS3D",
            "section_id": "101",
            "section_id2": "258",
            "section_id3": "429",
        },
    ),
    "rank": ("/news/news_list.naver", {"mode": "RANK"}),
    "photo": (
        "/news/news_list.naver",
        {"mode": "LSTD", "section_id": "101", "section_id2": "258", "type": "1"},
    ),
    "tv": ("/news/news_list.naver", {"mode": "TV", "section_id": "tv"}),
    "notice": ("/news/market_notice.naver", {}),
}


def fetch_news(code: str | None, *, kind: str, page: int, limit: int) -> dict:
    if kind == "search":
        raise SystemExit("--query is required for news search; use fetch_news_search()")
    if kind not in {"stock", "disclosure"}:
        return fetch_general_news(kind, page=page, limit=limit)
    if not code:
        raise SystemExit("--code is required for stock or disclosure news")
    code = normalize_stock_code(code)
    try:
        if kind == "stock":
            payload = front_json(
                "/news/list/integration",
                {"itemCode": code, "page": page, "pageSize": limit or 20},
                referer_path=f"/domestic/stock/{code}/total",
            )
            rows = (
                payload.get("stockNewsList", [])
                if isinstance(payload, dict)
                else payload
            )
        else:
            payload = front_json(
                "/stock/domestic/disclosure",
                {"code": code, "page": page, "pageSize": limit or 20},
                referer_path=f"/domestic/stock/{code}/notice",
            )
            rows = (
                payload.get("disclosures", payload)
                if isinstance(payload, dict)
                else payload
            )
        return {
            "source": "m.stock.naver.com public front-api JSON",
            "code": code,
            "kind": kind,
            "page": page,
            "rows": rows[:limit] if isinstance(rows, list) and limit else rows,
        }
    except Exception:
        pass

    if kind == "stock":
        path = "/item/news_news.naver"
        params = {"code": code, "page": page, "clusterId": ""}
    else:
        path = "/item/news_notice.naver"
        params = {"code": code, "page": page}
    html = pc_text(
        path, params, referer=f"https://finance.naver.com/item/news.naver?code={code}"
    )
    rows = []
    for table in extract_tables(html):
        if table["attrs"].get("class") != "type5":
            continue
        for row in table_to_records([["title", "provider", "date"], *table["rows"]]):
            if row.get("title"):
                rows.append(row)
    return {
        "source": "finance.naver.com public PC HTML table",
        "code": code,
        "kind": kind,
        "page": page,
        "rows": rows[:limit] if limit else rows,
    }


def fetch_general_news(kind: str, *, page: int, limit: int) -> dict:
    path, params = NEWS_KIND_PARAMS[kind]
    params = {**params, "page": page}
    html = pc_text(path, params)
    rows = (
        _extract_notice_rows(html) if kind == "notice" else _extract_article_links(html)
    )
    return {
        "source": "finance.naver.com public news HTML page",
        "kind": kind,
        "page": page,
        "rows": rows[:limit] if limit else rows,
    }


def fetch_news_search(query: str, *, page: int, limit: int) -> dict:
    html = pc_text("/news/news_search.naver", {"q": query, "page": page})
    rows = [
        row for row in _extract_article_links(html) if query in row.get("title", "")
    ]
    return {
        "source": "finance.naver.com public news search HTML page",
        "kind": "search",
        "query": query,
        "page": page,
        "rows": rows[:limit] if limit else rows,
        "note": "Naver's legacy news search page may include sidebar/ranking links; rows are filtered by query text in the title.",
    }


def _extract_article_links(html: str) -> list[dict[str, str]]:
    rows = []
    seen = set()
    for href, body in re.findall(
        r'<a[^>]+href="([^"]*/news/news_read\.naver[^"]*)"[^>]*>(.*?)</a>',
        html,
        flags=re.S,
    ):
        title = clean_cell(strip_tags(body))
        if not title or (title, href) in seen:
            continue
        seen.add((title, href))
        rows.append({"title": title, "url": href})
    return rows


def _extract_notice_rows(html: str) -> list[dict[str, str]]:
    rows = []
    for href, body in re.findall(
        r'<a[^>]+href="([^"]*/news/market_notice_read\.naver[^"]*)"[^>]*>(.*?)</a>',
        html,
        flags=re.S,
    ):
        title = clean_cell(strip_tags(body))
        if title:
            rows.append({"title": title, "url": href})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=normalize_stock_code)
    parser.add_argument(
        "--kind",
        choices=["stock", "disclosure", "search", *sorted(NEWS_KIND_PARAMS)],
        default="stock",
    )
    parser.add_argument("--query", help="Search query for --kind search")
    parser.add_argument("--page", type=int, default=1)
    add_limit_argument(parser, default=10)
    add_output_argument(parser)
    args = parser.parse_args()
    if args.kind == "search":
        if not args.query:
            raise SystemExit("--query is required for --kind search")
        payload = fetch_news_search(args.query, page=args.page, limit=args.limit)
    else:
        payload = fetch_news(
            args.code, kind=args.kind, page=args.page, limit=args.limit
        )
    emit_output(render_json(payload), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
