"""Step 2: Find related updates and documentation.

Extracts keywords from an update title and queries the database for other
updates whose titles share those keywords, providing contextual information
for downstream analysis steps.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import or_

from ingest.db.session import get_session
from ingest.models.update import Update

logger = logging.getLogger(__name__)

STOPWORDS: frozenset[str] = frozenset({
    "the", "a", "an", "is", "are", "for", "to", "in", "of", "and", "or",
    "with", "on", "at", "by", "from", "as", "it", "its", "this", "that",
    "these", "those", "has", "have", "had", "be", "been", "being", "was",
    "were", "will", "would", "can", "could", "should", "may", "might",
    "shall", "do", "does", "did", "not", "no", "now", "new", "also",
    "more", "about", "than", "into", "over", "such", "only", "just",
    "most", "very", "some", "any", "all", "each", "every", "few", "many",
    "much", "other", "both", "after", "before", "between", "through",
    "during", "without", "within", "under", "above", "below", "along",
    "across", "behind", "beyond",
})

_MAX_RELATED = 5


def extract_keywords(title: str) -> list[str]:
    """Extract meaningful keywords from an update title.

    Splits on whitespace, strips attached punctuation, drops common English
    stop-words, and keeps only words with three or more characters.
    Duplicates are removed while preserving the original order.
    """
    seen: set[str] = set()
    keywords: list[str] = []
    for word in title.split():
        cleaned = word.strip(".:;,!?()[]{}\"'")
        lower = cleaned.lower()
        if len(cleaned) >= 3 and lower not in STOPWORDS and lower not in seen:
            seen.add(lower)
            keywords.append(cleaned)
    return keywords


def find_related_context(update: Update) -> dict[str, Any]:
    """Find related updates by keyword-matching on titles.

    Extracts keywords from *update.title* and queries the database for
    other updates whose titles match any keyword via ``ILIKE``.  Results
    are ordered by ``published_date`` (most recent first) and capped at
    :data:`_MAX_RELATED`.

    Args:
        update: The :class:`~ingest.models.update.Update` instance to
            find related context for.

    Returns:
        A dict with ``keywords``, ``related_updates`` (list of summary
        dicts), and ``count``.
    """
    logger.info("Researching context for update %s", update.id)

    keywords = extract_keywords(update.title)
    if not keywords:
        logger.info("No keywords extracted from title: %r", update.title)
        return {"keywords": [], "related_updates": [], "count": 0}

    logger.debug("Extracted keywords: %s", keywords)

    with get_session() as session:
        filters = [Update.title.ilike(f"%{kw}%") for kw in keywords]
        related = (
            session.query(Update)
            .filter(Update.id != update.id)
            .filter(or_(*filters))
            .order_by(Update.published_date.desc().nullslast())
            .limit(_MAX_RELATED)
            .all()
        )

    related_updates: list[dict[str, Any]] = [
        {
            "id": str(r.id),
            "title": r.title,
            "source_url": r.source_url,
            "published_date": (
                r.published_date.isoformat() if r.published_date else None
            ),
            "summary": r.summary,
        }
        for r in related
    ]

    logger.info(
        "Found %d related updates for %r",
        len(related_updates),
        update.title,
    )

    return {
        "keywords": keywords,
        "related_updates": related_updates,
        "count": len(related_updates),
    }
