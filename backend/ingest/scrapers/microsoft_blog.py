"""Scraper for the Official Microsoft Blog (blogs.microsoft.com).

Strategy:
1. Try RSS feed first (most reliable), paginating with ``?paged=N``.
2. Fall back to scraping HTML listing pages at ``/page/N/``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import feedparser
from bs4 import BeautifulSoup

from .base import BaseScraper
from ..utils.parsing import parse_datetime, strip_html

logger = logging.getLogger(__name__)

BLOG_URL = "https://blogs.microsoft.com/"
BLOG_FEED_URL = "https://blogs.microsoft.com/feed/"
BASE_DOMAIN = "https://blogs.microsoft.com"
REQUEST_TIMEOUT = 30


class MicrosoftBlogScraper(BaseScraper):
    """Fetch and parse the Official Microsoft Blog.

    Strategy:
    1. Try RSS feed first (most reliable), paginating with ``?paged=N``.
    2. Fall back to scraping HTML listing pages at ``/page/N/``.
    """

    @property
    def source_name(self) -> str:
        return "microsoft-blog"

    def scrape(self) -> list[dict]:
        results = self._try_rss()
        if results:
            return results

        logger.info("RSS feed empty or unavailable, falling back to HTML scrape")
        return self._try_html()

    # ------------------------------------------------------------------
    # RSS path (with pagination)
    # ------------------------------------------------------------------

    def _try_rss(self) -> list[dict]:
        feed_url = self._discover_feed_url()
        if not feed_url:
            feed_url = BLOG_FEED_URL

        all_results: list[dict] = []
        seen_urls: set[str] = set()

        for page in range(1, self._max_pages + 1):
            paged_url = feed_url if page == 1 else f"{feed_url}?paged={page}"
            logger.info("Trying Microsoft Blog RSS feed page %d: %s", page, paged_url)

            try:
                resp = self._http.get(paged_url)
                resp.raise_for_status()
            except Exception as exc:
                if page == 1:
                    logger.warning("Could not fetch blog RSS feed: %s", exc)
                else:
                    logger.debug("RSS page %d unavailable (end of feed): %s", page, exc)
                break

            feed = feedparser.parse(resp.text)
            if feed.bozo and not feed.entries:
                if page == 1:
                    logger.warning("feedparser error on blog feed: %s", feed.bozo_exception)
                break

            if not feed.entries:
                logger.debug("RSS page %d returned 0 entries, stopping", page)
                break

            page_results = self._parse_feed_entries(feed.entries, seen_urls)
            if not page_results:
                logger.debug("RSS page %d had no new entries, stopping", page)
                break

            all_results.extend(page_results)

        logger.info("Parsed %d total entries from Microsoft Blog RSS", len(all_results))
        return all_results

    def _parse_feed_entries(
        self, entries: list, seen_urls: set[str]
    ) -> list[dict]:
        """Parse feed entries, skipping URLs already seen across pages."""
        results: list[dict] = []
        for entry in entries:
            url = entry.get("link", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            published = self._parse_published(entry)
            categories = [t.term for t in getattr(entry, "tags", []) if hasattr(t, "term")]

            results.append(
                {
                    "title": entry.get("title", ""),
                    "source_url": url,
                    "published_date": published,
                    "summary": strip_html(entry.get("summary", "")),
                    "categories": categories or None,
                    "raw_data": dict(entry),
                }
            )
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
                href = BASE_DOMAIN + href
            logger.info("Discovered blog RSS feed URL: %s", href)
            return href
        return None

    # ------------------------------------------------------------------
    # HTML scrape fallback (with pagination via /page/N/)
    # ------------------------------------------------------------------

    def _try_html(self) -> list[dict]:
        all_results: list[dict] = []
        seen_urls: set[str] = set()

        for page in range(1, self._max_pages + 1):
            page_url = BLOG_URL if page == 1 else f"{BLOG_URL}page/{page}/"
            logger.info("Scraping Microsoft Blog HTML page %d: %s", page, page_url)

            try:
                resp = self._http.get(page_url)
                resp.raise_for_status()
            except Exception as exc:
                logger.error("Failed to fetch blog page: %s", exc)
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            page_results = self._parse_html_articles(soup, seen_urls)

            if not page_results:
                logger.debug("HTML page %d had no new articles, stopping", page)
                break

            all_results.extend(page_results)

        logger.info("Parsed %d total entries from Microsoft Blog HTML", len(all_results))
        return all_results

    def _parse_html_articles(
        self, soup: BeautifulSoup, seen_urls: set[str]
    ) -> list[dict]:
        """Extract articles from a single HTML listing page.

        Microsoft Blog uses ``<article>`` tags with ``<h3>`` titles and
        ``<time datetime="...">`` elements.  The post link is the second
        ``<a>`` inside the article (the first is often the author link).
        """
        results: list[dict] = []

        articles = soup.select("article")
        if not articles:
            articles = soup.select(".post-item") or soup.select(".card")

        for article in articles:
            # Title — usually in h3.c-heading-4
            title_tag = article.find(["h3", "h2", "h4"])
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)

            # Link — find the <a> that wraps the title or points to the post
            link_tag = title_tag.find("a") or title_tag.parent if title_tag.parent and title_tag.parent.name == "a" else None
            if not link_tag:
                # Fall back to looking for any <a> with /blog/YYYY/ pattern
                for a_tag in article.find_all("a"):
                    href = a_tag.get("href", "")
                    if "/blog/20" in href:
                        link_tag = a_tag
                        break

            href = ""
            if link_tag:
                href = link_tag.get("href", "") if hasattr(link_tag, "get") else ""
            if href and href.startswith("/"):
                href = BASE_DOMAIN + href

            if not href or href in seen_urls:
                continue
            seen_urls.add(href)

            # Date
            time_tag = article.find("time")
            published = None
            if time_tag:
                published = parse_datetime(
                    time_tag.get("datetime") or time_tag.get_text(strip=True)
                )

            results.append(
                {
                    "title": title,
                    "source_url": href,
                    "published_date": published,
                    "summary": "",
                    "categories": None,
                    "raw_data": {"html_snippet": str(article)[:2000]},
                }
            )

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
