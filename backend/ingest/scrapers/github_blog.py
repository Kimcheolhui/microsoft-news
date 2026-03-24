"""Scraper for the GitHub Blog."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from urllib.parse import urljoin

import feedparser
from bs4 import BeautifulSoup

from .base import BaseScraper
from ..utils.parsing import parse_datetime, strip_html

logger = logging.getLogger(__name__)

BLOG_URL = "https://github.blog/"
COMMON_FEED_PATHS = ["/feed/", "/rss/", "/blog/feed/"]
REQUEST_TIMEOUT = 30


class GitHubBlogScraper(BaseScraper):
    """Fetch and parse GitHub Blog posts.

    Strategy:
    1. Try RSS feed first (most reliable).
    2. Fall back to scraping the HTML listing page.
    """

    @property
    def source_name(self) -> str:
        return "github-blog"

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
            feed_url = self._probe_common_feed_paths()

        if not feed_url:
            logger.warning("No RSS feed found for GitHub Blog")
            return []

        logger.info("Trying GitHub Blog RSS feed: %s", feed_url)
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

        logger.info("Parsed %d entries from GitHub Blog RSS", len(results))
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
                href = urljoin(BLOG_URL, href)
            logger.info("Discovered blog RSS feed URL: %s", href)
            return href
        return None

    def _probe_common_feed_paths(self) -> str | None:
        """Try common feed paths and return the first that responds with valid XML."""
        for path in COMMON_FEED_PATHS:
            url = urljoin(BLOG_URL, path)
            try:
                resp = self._http.get(url)
                if resp.ok and ("xml" in resp.headers.get("content-type", "") or "<rss" in resp.text[:500]):
                    logger.info("Found feed at common path: %s", url)
                    return url
            except Exception:
                continue
        return None

    # ------------------------------------------------------------------
    # HTML scrape fallback
    # ------------------------------------------------------------------

    def _try_html(self) -> list[dict]:
        logger.info("Scraping GitHub Blog HTML: %s", BLOG_URL)
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
                href = urljoin(BLOG_URL, href)

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

        logger.info("Parsed %d entries from GitHub Blog HTML", len(results))
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
