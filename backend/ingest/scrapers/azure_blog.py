"""Scraper for the Azure Blog."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import feedparser
from bs4 import BeautifulSoup

from .base import BaseScraper
from ..utils.parsing import parse_datetime, strip_html

logger = logging.getLogger(__name__)

BLOG_URL = "https://azure.microsoft.com/en-us/blog/"
BLOG_FEED_URL = "https://azure.microsoft.com/en-us/blog/feed/"
REQUEST_TIMEOUT = 30


class AzureBlogScraper(BaseScraper):
    """Fetch and parse Azure Blog posts.

    Strategy:
    1. Try RSS feed first (most reliable).
    2. Fall back to scraping the HTML listing page.
    """

    @property
    def source_name(self) -> str:
        return "azure-blog"

    def scrape(self) -> list[dict]:
        results = self._try_rss()
        if results:
            return results

        logger.info("RSS feed empty or unavailable, falling back to HTML scrape")
        return self._try_html()

    # ------------------------------------------------------------------
    # RSS path
    # ------------------------------------------------------------------

    def _try_rss(self) -> list[dict]:
        feed_url = self._discover_feed_url()
        if not feed_url:
            feed_url = BLOG_FEED_URL

        logger.info("Trying Azure Blog RSS feed: %s", feed_url)
        try:
            resp = self._http.get(feed_url)
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("Could not fetch blog RSS feed: %s", exc)
            return []

        feed = feedparser.parse(resp.text)
        if feed.bozo and not feed.entries:
            logger.warning("feedparser error on blog feed: %s", feed.bozo_exception)
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

        logger.info("Parsed %d entries from Azure Blog RSS", len(results))
        return results

    def _discover_feed_url(self) -> str | None:
        """Look for an RSS <link> tag in the blog HTML head."""
        try:
            resp = self._http.get(BLOG_URL)
            resp.raise_for_status()
        except Exception:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        link = soup.find("link", attrs={"type": "application/rss+xml"})
        if link and link.get("href"):
            href = link["href"]
            if href.startswith("/"):
                href = "https://azure.microsoft.com" + href
            logger.info("Discovered blog RSS feed URL: %s", href)
            return href
        return None

    # ------------------------------------------------------------------
    # HTML scrape fallback
    # ------------------------------------------------------------------

    def _try_html(self) -> list[dict]:
        logger.info("Scraping Azure Blog HTML: %s", BLOG_URL)
        try:
            resp = self._http.get(BLOG_URL)
            resp.raise_for_status()
        except Exception as exc:
            logger.error("Failed to fetch blog page: %s", exc)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        results: list[dict] = []

        # Try common article selectors
        articles = (
            soup.select("article")
            or soup.select(".post-item")
            or soup.select("[data-bi-area='blog-post']")
            or soup.select(".card")
        )

        for article in articles:
            title_tag = article.find(["h2", "h3", "h4"]) or article.find("a")
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            link_tag = title_tag if title_tag.name == "a" else title_tag.find("a")
            href = link_tag["href"] if link_tag and link_tag.get("href") else ""
            if href and href.startswith("/"):
                href = "https://azure.microsoft.com" + href

            time_tag = article.find("time")
            published = None
            if time_tag:
                published = parse_datetime(
                    time_tag.get("datetime") or time_tag.get_text(strip=True)
                )

            summary_tag = article.find("p")
            summary = summary_tag.get_text(strip=True) if summary_tag else ""

            results.append(
                {
                    "title": title,
                    "source_url": href,
                    "published_date": published,
                    "summary": summary,
                    "categories": None,
                    "raw_data": {"html_snippet": str(article)[:2000]},
                }
            )

        logger.info("Parsed %d entries from Azure Blog HTML", len(results))
        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_published(entry) -> datetime | None:
        for field in ("published", "updated"):
            val = entry.get(field)
            if val:
                dt = parse_datetime(val)
                if dt is not None:
                    return dt
        for field in ("published_parsed", "updated_parsed"):
            st = entry.get(field)
            if st:
                try:
                    return datetime(*st[:6], tzinfo=timezone.utc)
                except Exception:
                    pass
        return None
