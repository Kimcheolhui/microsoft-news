"""Step 1: Full content scraping for analysis.

Fetches a web page, strips non-content HTML, and returns clean text sized
for LLM consumption.  The interface is intentionally simple so the
implementation can later be swapped for a Bing Search–backed variant.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from analysis.utils.content_parser import html_to_text, truncate_for_llm

logger = logging.getLogger(__name__)

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; AzureUpdateBot/1.0; "
        "+https://github.com/azure-new)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

_TIMEOUT = 30
_MAX_RETRIES = 2
_BACKOFF_BASE = 2  # seconds
_TRANSIENT_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


def scrape_full_content(source_url: str) -> dict[str, Any]:
    """Scrape the full article content from *source_url*.

    Fetches the page HTML, converts it to clean text via
    :func:`~analysis.utils.content_parser.html_to_text`, and truncates to
    a size suitable for LLM consumption.

    The function retries up to ``_MAX_RETRIES`` times on transient HTTP
    errors (timeouts, 5xx, 429) with exponential back-off.

    Args:
        source_url: The URL to scrape.

    Returns:
        On success::

            {"url": str, "raw_length": int, "text": str, "truncated": bool}

        On failure::

            {"url": str, "error": str, "text": ""}
    """
    logger.info("Scraping full content from %s", source_url)

    last_error: str | None = None

    for attempt in range(_MAX_RETRIES + 1):
        try:
            if attempt > 0:
                wait = _BACKOFF_BASE ** attempt
                logger.info(
                    "Retry %d/%d after %ds for %s",
                    attempt, _MAX_RETRIES, wait, source_url,
                )
                time.sleep(wait)

            response = requests.get(
                source_url,
                headers=_DEFAULT_HEADERS,
                timeout=_TIMEOUT,
            )

            # Retry on transient server / rate-limit errors
            if response.status_code in _TRANSIENT_STATUS_CODES:
                last_error = f"HTTP {response.status_code}"
                logger.warning(
                    "Transient error %s for %s", last_error, source_url,
                )
                continue

            response.raise_for_status()

            clean_text = html_to_text(response.text)
            raw_length = len(clean_text)
            truncated_text = truncate_for_llm(clean_text)

            result: dict[str, Any] = {
                "url": source_url,
                "raw_length": raw_length,
                "text": truncated_text,
                "truncated": truncated_text != clean_text,
            }
            logger.info(
                "Scraped %s: %d chars (truncated=%s)",
                source_url,
                raw_length,
                result["truncated"],
            )
            return result

        except requests.exceptions.RequestException as exc:
            last_error = str(exc)
            # Only retry on connection / timeout errors
            if isinstance(
                exc,
                (requests.exceptions.ConnectionError, requests.exceptions.Timeout),
            ):
                logger.warning(
                    "Transient error for %s: %s", source_url, last_error,
                )
                continue
            # Non-transient (e.g. InvalidURL) — stop immediately
            break

    logger.error("Failed to scrape %s: %s", source_url, last_error)
    return {"url": source_url, "error": last_error or "Unknown error", "text": ""}
