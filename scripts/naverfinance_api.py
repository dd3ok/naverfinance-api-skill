#!/usr/bin/env python3
"""Shared helpers for public read-only NaverFinance web data scripts."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


MOBILE_BASE_URL = "https://m.stock.naver.com"
STOCK_API_BASE_URL = "https://api.stock.naver.com"
PC_BASE_URL = "https://finance.naver.com"
POLLING_BASE_URL = "https://polling.finance.naver.com"
WISEREPORT_BASE_URL = "https://navercomp.wisereport.co.kr/v2"
LEGACY_API_BASE_URL = "https://api.finance.naver.com"
DEFAULT_TIMEOUT = 30
ALLOWED_PUBLIC_HOSTS = {
    "api.finance.naver.com",
    "api.stock.naver.com",
    "finance.naver.com",
    "m.stock.naver.com",
    "navercomp.wisereport.co.kr",
    "polling.finance.naver.com",
}
SENSITIVE_PATH_MARKERS = {
    "account",
    "auth",
    "balance",
    "cookie",
    "holding",
    "my",
    "order",
    "payment",
    "token",
    "userinfo",
}
SENSITIVE_QUERY_KEYS = SENSITIVE_PATH_MARKERS | {
    "access_token",
    "accesstoken",
    "accountno",
    "auth_token",
    "authtoken",
    "authorization",
    "orderno",
    "refresh_token",
    "refreshtoken",
    "user_info",
}


def normalize_stock_code(code: str) -> str:
    value = code.strip().upper()
    if value.startswith("A") and len(value) == 7 and value[1:].isdigit():
        value = value[1:]
    if not (len(value) == 6 and value.isdigit()):
        raise argparse.ArgumentTypeError("Korean stock code must be six digits")
    return value


def normalize_index_code(code: str) -> str:
    value = code.strip().upper()
    aliases = {
        "KOSPI200": "KPI200",
        "KOSPI": "KOSPI",
        "KOSDAQ": "KOSDAQ",
        "KPI200": "KPI200",
    }
    return aliases.get(value, value)


def build_path(path: str, params: dict[str, Any] | None = None) -> str:
    if not params:
        return path
    query = urllib.parse.urlencode(
        {key: _query_value(value) for key, value in params.items() if value is not None}
    )
    return f"{path}?{query}" if query else path


def request_bytes(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    referer: str | None = None,
    accept: str = "*/*",
) -> tuple[bytes, str]:
    _validate_public_url(url)
    headers = {
        "Accept": accept,
        "User-Agent": "Mozilla/5.0 naverfinance-web-api-skill/1.0",
    }
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            return resp.read(), content_type
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        raise RuntimeError(
            f"Naver endpoint returned HTTP {exc.code}: {detail}"
        ) from exc


def _validate_public_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in ALLOWED_PUBLIC_HOSTS:
        raise RuntimeError(
            f"Unsupported Naver public host: {host or parsed.netloc or '<missing>'}"
        )
    path_markers = _sensitive_path_markers(parsed.path)
    if path_markers:
        joined = ", ".join(sorted(path_markers))
        raise RuntimeError(f"Blocked sensitive Naver URL path marker: {joined}")
    query_markers = _sensitive_query_keys(parsed.query)
    if query_markers:
        joined = ", ".join(sorted(query_markers))
        raise RuntimeError(f"Blocked sensitive Naver URL query key: {joined}")


def _sensitive_path_markers(path: str) -> set[str]:
    markers: set[str] = set()
    decoded = urllib.parse.unquote(path).lower()
    for segment in decoded.split("/"):
        if not segment:
            continue
        compact = re.sub(r"[^a-z0-9]", "", segment)
        tokens = {segment, compact}
        tokens.update(token for token in re.split(r"[^a-z0-9]+", segment) if token)
        markers.update(token for token in tokens if token in SENSITIVE_PATH_MARKERS)
        for marker in SENSITIVE_PATH_MARKERS - {"my"}:
            if compact.startswith(marker):
                markers.add(marker)
    return markers


def _sensitive_query_keys(query: str) -> set[str]:
    markers: set[str] = set()
    for key, _value in urllib.parse.parse_qsl(query, keep_blank_values=True):
        lowered = key.lower()
        compact = re.sub(r"[^a-z0-9]", "", lowered)
        if lowered in SENSITIVE_QUERY_KEYS or compact in SENSITIVE_QUERY_KEYS:
            markers.add(lowered)
    return markers


def request_text(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    referer: str | None = None,
    accept: str = "*/*",
) -> str:
    raw, content_type = request_bytes(
        url, timeout=timeout, referer=referer, accept=accept
    )
    encoding = _encoding_from_content_type(content_type) or "utf-8"
    try:
        return raw.decode(encoding)
    except UnicodeDecodeError:
        for fallback in ("utf-8", "euc-kr", "cp949"):
            try:
                return raw.decode(fallback)
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="replace")


def request_json_url(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    referer: str | None = None,
) -> Any:
    text = request_text(
        url,
        timeout=timeout,
        referer=referer,
        accept="application/json, text/plain, */*",
    )
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        preview = text[:500].replace("\n", " ")
        raise RuntimeError(f"Expected JSON but got: {preview}") from exc


def mobile_json(
    path: str, params: dict[str, Any] | None = None, *, referer_path: str = "/"
) -> Any:
    return request_json_url(
        MOBILE_BASE_URL + build_path(path, params),
        referer=MOBILE_BASE_URL + referer_path,
    )


def front_json(
    path: str, params: dict[str, Any] | None = None, *, referer_path: str = "/"
) -> Any:
    payload = mobile_json("/front-api" + path, params, referer_path=referer_path)
    if isinstance(payload, dict) and "isSuccess" in payload:
        if payload.get("isSuccess") is True and "result" in payload:
            return payload["result"]
        detail = payload.get("detailCode") or payload.get("code") or "unknown"
        message = (
            payload.get("message")
            or payload.get("error")
            or "Naver front-api request failed"
        )
        raise RuntimeError(f"Naver front-api error {detail}: {message}")
    return payload


def pc_text(
    path: str, params: dict[str, Any] | None = None, *, referer: str | None = None
) -> str:
    full_path = build_path(path, params)
    return request_text(PC_BASE_URL + full_path, referer=referer or PC_BASE_URL + "/")


def wisereport_text(path: str, params: dict[str, Any] | None = None) -> str:
    return request_text(
        WISEREPORT_BASE_URL + build_path(path, params), referer=PC_BASE_URL + "/"
    )


def extract_tables(markup: str) -> list[dict[str, Any]]:
    parser = _TableParser()
    parser.feed(markup)
    return parser.tables


def first_nonempty_table(markup: str, *, min_columns: int = 2) -> list[list[str]]:
    for table in extract_tables(markup):
        rows = [
            row
            for row in table["rows"]
            if len([cell for cell in row if cell.strip()]) >= min_columns
        ]
        if rows:
            return rows
    return []


def table_to_records(rows: list[list[str]]) -> list[dict[str, str]]:
    if not rows:
        return []
    header = [clean_cell(value) or f"col{idx + 1}" for idx, value in enumerate(rows[0])]
    records: list[dict[str, str]] = []
    for row in rows[1:]:
        if not any(cell.strip() for cell in row):
            continue
        padded = row + [""] * max(0, len(header) - len(row))
        records.append(
            {
                header[idx]: clean_cell(value)
                for idx, value in enumerate(padded[: len(header)])
            }
        )
    return records


def clean_cell(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def strip_tags(markup: str) -> str:
    text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", markup)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return clean_cell(text)


def render_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def emit_output(text: str, output_path: str | None) -> None:
    if output_path:
        Path(output_path).write_text(text, encoding="utf-8")
    else:
        print(text, end="" if text.endswith("\n") else "\n")


def add_output_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output", help="Write JSON output to this path")


def add_limit_argument(parser: argparse.ArgumentParser, default: int = 10) -> None:
    parser.add_argument(
        "--limit", type=int, default=default, help="Maximum rows/items to include"
    )


def _query_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _encoding_from_content_type(content_type: str) -> str | None:
    match = re.search(r"charset=([^;\s]+)", content_type, flags=re.I)
    return match.group(1) if match else None


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[dict[str, Any]] = []
        self._in_table = False
        self._in_cell = False
        self._current_table: dict[str, Any] | None = None
        self._current_row: list[str] | None = None
        self._current_cell: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table":
            self._in_table = True
            self._current_table = {"attrs": dict(attrs), "rows": []}
        elif self._in_table and tag == "tr":
            self._current_row = []
        elif self._in_table and tag in {"td", "th"}:
            self._in_cell = True
            self._current_cell = []
        elif self._in_cell and tag in {"br", "p", "div"}:
            self._current_cell.append(" ")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._in_table and tag in {"td", "th"} and self._in_cell:
            if self._current_row is not None:
                self._current_row.append(clean_cell("".join(self._current_cell)))
            self._in_cell = False
            self._current_cell = []
        elif self._in_table and tag == "tr":
            if self._current_table is not None and self._current_row is not None:
                self._current_table["rows"].append(self._current_row)
            self._current_row = None
        elif tag == "table" and self._in_table:
            if self._current_table is not None:
                self.tables.append(self._current_table)
            self._in_table = False
            self._current_table = None

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._current_cell.append(data)


def main() -> int:
    print("Shared module; run one of the task scripts instead.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
