#!/usr/bin/env python3
"""Fetch public NaverFinance home summary widgets."""

from __future__ import annotations

import argparse
from typing import Any

from naverfinance_api import (
    PC_BASE_URL,
    add_limit_argument,
    add_output_argument,
    emit_output,
    render_json,
    request_json_url,
)


REPEATED_SECTIONS = {
    "topItems",
    "nxtTopItems",
    "groupTopList",
    "themeTopList",
    "searchList",
    "todayIndexDealTrendList",
    "todayIndexItemList",
}


def fetch_home_summary(*, limit: int) -> dict[str, Any]:
    payload = request_json_url(
        PC_BASE_URL + "/main/mainSummary.naver",
        referer=PC_BASE_URL + "/",
    )
    result: dict[str, Any] = {}
    if isinstance(payload, dict):
        message = payload.get("message")
        if isinstance(message, dict):
            inner = message.get("result")
            if isinstance(inner, dict):
                result = inner
    summary = {
        key: _limit_section(value, limit) if key in REPEATED_SECTIONS else value
        for key, value in result.items()
    }
    for key in REPEATED_SECTIONS:
        summary.setdefault(key, [])
    return {
        "source": "finance.naver.com public mainSummary JSON",
        "summary": summary,
    }


def _limit_section(value: Any, limit: int) -> Any:
    if not limit or not isinstance(value, list):
        return value
    if value and all(isinstance(item, list) for item in value):
        return [item[:limit] for item in value]
    return value[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_limit_argument(parser, default=5)
    add_output_argument(parser)
    args = parser.parse_args()
    emit_output(render_json(fetch_home_summary(limit=args.limit)), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
