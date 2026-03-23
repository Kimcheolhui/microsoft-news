"""Date and HTML parsing helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser


def strip_html(html: str) -> str:
    """Remove HTML tags and return plain text."""
    return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)


def parse_datetime(value: str | None) -> datetime | None:
    """Best-effort parse of a datetime string to timezone-aware UTC."""
    if not value:
        return None

    # Try RFC-2822 (common in RSS feeds)
    from email.utils import parsedate_to_datetime

    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass

    # Try ISO-8601
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass

    # Fallback to python-dateutil fuzzy parsing
    try:
        dt = dateutil_parser.parse(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None
