"""Scraper for Microsoft Tech Community blogs.

Tech Community is a React SPA backed by Khoros/Lithium.  The server-side
rendered ``__NEXT_DATA__`` payload contains an Apollo cache with blog posts
for each board page, so no headless browser is needed.

We scrape a curated list of Azure-related blog boards and aggregate posts
from all of them.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper
from ..utils.parsing import parse_datetime, strip_html

logger = logging.getLogger(__name__)

BASE_URL = "https://techcommunity.microsoft.com"

# Azure-related blog boards on Tech Community.
# Each tuple is (board_display_id, human_label).
BLOG_BOARDS: list[tuple[str, str]] = [
    ("AzureInfrastructureBlog", "Azure Infrastructure Blog"),
    ("AppsonAzureBlog", "Apps on Azure Blog"),
    ("AzureAIServicesBlog", "Azure AI Services Blog"),
    ("AzureDatabasesMigrationBlog", "Azure Databases Blog"),
    ("AzureDevCommunity", "Azure Dev Community"),
    ("AzureGovernanceandManagementBlog", "Azure Governance Blog"),
    ("AzureNetworkingBlog", "Azure Networking Blog"),
    ("AzureObservabilityBlog", "Azure Observability Blog"),
    ("AzureSecurityBlog", "Azure Security Blog"),
    ("AzureStorageBlog", "Azure Storage Blog"),
    ("FastTrackforAzureBlog", "FastTrack for Azure Blog"),
    ("FinancialServicesBlog", "Financial Services Blog"),
]


class TechCommunityScraper(BaseScraper):
    """Scrape blog posts from multiple Azure-related Tech Community boards.

    Data is extracted from the ``__NEXT_DATA__`` JSON embedded in each
    board listing page.  Each board page contains ~10 recent posts.
    """

    @property
    def source_name(self) -> str:
        return "microsoft-tech-community"

    def scrape(self) -> list[dict]:
        all_results: list[dict] = []
        seen_urls: set[str] = set()

        for board_id, label in BLOG_BOARDS:
            page_url = f"{BASE_URL}/t5/{board_id.lower()}/bg-p/{board_id}"
            logger.info("Scraping Tech Community board: %s", label)

            try:
                posts = self._scrape_board(page_url, seen_urls)
                all_results.extend(posts)
                logger.info("  %s: %d posts", label, len(posts))
            except Exception as exc:
                logger.warning("Failed to scrape board %s: %s", board_id, exc)

        logger.info(
            "Parsed %d total entries from Tech Community (%d boards)",
            len(all_results),
            len(BLOG_BOARDS),
        )
        return all_results

    def _scrape_board(
        self, page_url: str, seen_urls: set[str]
    ) -> list[dict]:
        """Extract blog posts from a single board listing page."""
        resp = self._http.get(page_url)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if not script or not script.string:
            logger.debug("No __NEXT_DATA__ found on %s", page_url)
            return []

        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in __NEXT_DATA__ on %s", page_url)
            return []

        apollo = (
            data.get("props", {}).get("pageProps", {}).get("apolloState", {})
        )
        if not apollo:
            return []

        results: list[dict] = []

        for key, entry in apollo.items():
            if not key.startswith("BlogTopicMessage:"):
                continue

            uid = entry.get("uid")
            subject = entry.get("subject", "")
            if not uid or not subject:
                continue

            # Construct the canonical post URL.
            board_ref = entry.get("board", {}).get("__ref", "")
            board_id = board_ref.replace("Blog:board:", "") if board_ref else ""
            post_url = f"{BASE_URL}/t5/{board_id}/ba-p/{uid}"

            if post_url in seen_urls:
                continue
            seen_urls.add(post_url)

            # Extract teaser/body summary.
            summary = self._extract_summary(entry)

            published = self._parse_post_time(entry)

            results.append(
                {
                    "title": subject,
                    "source_url": post_url,
                    "published_date": published,
                    "summary": summary,
                    "categories": None,
                    "raw_data": {
                        "board_id": board_id,
                        "uid": uid,
                        "views": entry.get("metrics", {}).get("views"),
                        "kudos": entry.get("kudosSumWeight"),
                        "replies": entry.get("repliesCount"),
                    },
                }
            )

        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_summary(entry: dict) -> str:
        """Best-effort extraction of a short summary from the apollo entry."""
        # Try the 'introduction' field first (short tagline).
        intro = entry.get("introduction")
        if intro:
            return strip_html(intro)

        # Fall back to the truncated body strip.
        for key in entry:
            if key.startswith("body@stripHtml"):
                val = entry[key]
                if isinstance(val, str) and val.strip():
                    return val.strip()

        return ""

    @staticmethod
    def _parse_post_time(entry: dict) -> datetime | None:
        """Parse postTime or lastPublishTime from the apollo entry."""
        for field in ("postTime", "lastPublishTime"):
            val = entry.get(field)
            if not val:
                continue
            dt = parse_datetime(val)
            if dt is not None:
                return dt
        return None
