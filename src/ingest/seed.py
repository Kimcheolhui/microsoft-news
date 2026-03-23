"""Seed default sources into the database."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from .models import Source

logger = logging.getLogger(__name__)

DEFAULT_SOURCES = [
    {
        "name": "azure-updates-rss",
        "url": "https://www.microsoft.com/releasecommunications/api/v2/azure/rss",
        "source_type": "rss",
    },
    {
        "name": "azure-blog",
        "url": "https://azure.microsoft.com/en-us/blog/",
        "source_type": "web",
    },
    {
        "name": "fabric-blog",
        "url": "https://blog.fabric.microsoft.com/",
        "source_type": "web",
        "enabled": False,
    },
    {
        "name": "github-blog",
        "url": "https://github.blog/",
        "source_type": "web",
        "enabled": False,
    },
]


def seed_sources(session: Session) -> int:
    """Insert default sources if they don't already exist.

    Returns the number of new sources created.
    """
    created = 0
    for src in DEFAULT_SOURCES:
        exists = session.query(Source).filter_by(name=src["name"]).first()
        if exists:
            logger.debug("Source %r already exists, skipping", src["name"])
            continue

        source = Source(
            id=uuid.uuid4(),
            name=src["name"],
            url=src["url"],
            source_type=src["source_type"],
            enabled=src.get("enabled", True),
        )
        session.add(source)
        created += 1
        logger.info("Seeded source: %s", src["name"])

    session.flush()
    return created
