"""Scraper for the Azure Updates RSS feed."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import feedparser
import requests

from .base import BaseScraper
from ..utils.parsing import parse_datetime, strip_html

logger = logging.getLogger(__name__)

FEED_URL = "https://www.microsoft.com/releasecommunications/api/v2/azure/rss"
REQUEST_TIMEOUT = 30


class AzureUpdatesRssScraper(BaseScraper):
    """Fetch and parse the Azure Updates RSS feed."""

    @property
    def source_name(self) -> str:
        return "azure-updates-rss"

    def scrape(self) -> list[dict]:
        logger.info("Fetching Azure Updates RSS feed: %s", FEED_URL)
        try:
            resp = requests.get(FEED_URL, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Failed to fetch RSS feed: %s", exc)
            return []

        feed = feedparser.parse(resp.text)
        if feed.bozo and not feed.entries:
            logger.error("feedparser error: %s", feed.bozo_exception)
            return []

        results: list[dict] = []
        for entry in feed.entries:
            published = self._parse_published(entry)
            categories = [t.term for t in getattr(entry, "tags", []) if hasattr(t, "term")]

            results.append(
                {
                    "title": entry.get("title", ""),
                    "source_url": entry.get("link", ""),
                    "published_date": published,
                    "summary": strip_html(entry.get("summary", "")),
                    "categories": categories or None,
                    "raw_data": dict(entry),
                }
            )

        logger.info("Parsed %d entries from Azure Updates RSS", len(results))
        return results

    @staticmethod
    def _parse_published(entry) -> datetime | None:
        for field in ("published", "updated"):
            val = entry.get(field)
            if val:
                dt = parse_datetime(val)
                if dt is not None:
                    return dt
        # feedparser also provides *_parsed as time.struct_time
        for field in ("published_parsed", "updated_parsed"):
            st = entry.get(field)
            if st:
                try:
                    return datetime(*st[:6], tzinfo=timezone.utc)
                except Exception:
                    pass
        return None
