"""Step 3: LLM analysis of update content."""

from __future__ import annotations

import logging
import time

from ingest.models.update import Update

from analysis.agents.client import analysis_session, send_message
from analysis.prompts.analysis import ANALYSIS_SYSTEM_PROMPT, ANALYSIS_USER_TEMPLATE
from analysis.utils.json_parser import extract_json

logger = logging.getLogger(__name__)

_EXPECTED_KEYS = (
    "update_type",
    "affected_services",
    "impact_summary",
    "key_details",
    "action_items",
)


def _format_related_updates(research_data: dict) -> str:
    """Build a human-readable string of related updates from research data."""
    related: list[dict] = research_data.get("related_updates", [])
    if not related:
        return "None found."

    lines: list[str] = []
    for item in related:
        title = item.get("title", "Untitled")
        date = item.get("published_date", "N/A")
        url = item.get("source_url", "")
        summary = item.get("summary") or ""
        entry = f"- {title} ({date})"
        if url:
            entry += f"  {url}"
        if summary:
            entry += f"\n  {summary}"
        lines.append(entry)
    return "\n".join(lines)


def _build_content(update: Update, scraped_content: dict) -> str:
    """Return the best available content for the prompt."""
    if scraped_content.get("error") or not scraped_content.get("text"):
        # Fallback to data stored on the update itself
        parts: list[str] = []
        if update.summary:
            parts.append(update.summary)
        if update.body:
            parts.append(update.body)
        return "\n\n".join(parts) if parts else "(No content available.)"
    return scraped_content["text"]


async def analyze_update(
    update: Update,
    scraped_content: dict,
    research_data: dict,
) -> dict:
    """Run LLM analysis on the scraped content and research context.

    Args:
        update: The :class:`Update` being analysed.
        scraped_content: Dict returned by the deep-scraper step.
        research_data: Dict returned by the researcher step.

    Returns:
        A dict with parsed analysis fields, ``raw_response``, and optionally
        ``parse_error`` when the LLM output could not be parsed as JSON.
    """
    logger.info("Analyzing update %s – %s", update.id, update.title)
    start = time.monotonic()

    content = _build_content(update, scraped_content)
    related_updates = _format_related_updates(research_data)

    user_message = ANALYSIS_USER_TEMPLATE.format(
        title=update.title,
        published_date=update.published_date or "Unknown",
        source_url=update.source_url,
        content=content,
        related_updates=related_updates,
    )

    async with analysis_session(system_message=ANALYSIS_SYSTEM_PROMPT) as session:
        raw_response = await send_message(session, user_message)

    elapsed = time.monotonic() - start
    logger.info("Analysis completed in %.1fs (%d chars)", elapsed, len(raw_response))

    parsed = extract_json(raw_response)
    if parsed is None:
        logger.warning("Failed to parse analysis JSON for update %s", update.id)
        return {
            "update_type": "update",
            "affected_services": [],
            "impact_summary": "",
            "key_details": [],
            "action_items": [],
            "raw_response": raw_response,
            "parse_error": "Could not extract valid JSON from model response",
        }

    result: dict = {key: parsed.get(key, [] if key in ("affected_services", "key_details", "action_items") else "") for key in _EXPECTED_KEYS}
    result["raw_response"] = raw_response
    return result
