"""Scraper registry."""

from __future__ import annotations

from .base import BaseScraper
from .azure_updates_rss import AzureUpdatesRssScraper
from .azure_blog import AzureBlogScraper

SCRAPERS: dict[str, type[BaseScraper]] = {
    "azure-updates-rss": AzureUpdatesRssScraper,
    "azure-blog": AzureBlogScraper,
}


def get_scraper(source_name: str) -> BaseScraper:
    """Return an instantiated scraper for the given source name."""
    cls = SCRAPERS.get(source_name)
    if cls is None:
        raise KeyError(
            f"No scraper registered for {source_name!r}. "
            f"Available: {', '.join(SCRAPERS)}"
        )
    return cls()
