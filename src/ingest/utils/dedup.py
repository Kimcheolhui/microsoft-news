"""Deduplication logic for ingested updates."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import Update


def is_duplicate(source_url: str, existing_urls: set[str]) -> bool:
    """Check if a URL has already been ingested."""
    return source_url in existing_urls


def find_existing_urls(session: Session, urls: list[str]) -> set[str]:
    """Return set of source_urls that already exist in the updates table."""
    if not urls:
        return set()
    rows = (
        session.query(Update.source_url)
        .filter(Update.source_url.in_(urls))
        .all()
    )
    return {row[0] for row in rows}
