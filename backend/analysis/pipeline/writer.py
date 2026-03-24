"""Step 4: LLM report generation."""

from __future__ import annotations

import json
import logging
import time

from ingest.models.update import Update

from analysis.agents.client import analysis_session, send_message
from analysis.prompts.writing import WRITING_SYSTEM_PROMPT, WRITING_USER_TEMPLATE
from analysis.utils.json_parser import extract_json

logger = logging.getLogger(__name__)

_EXPECTED_KEYS = (
    "title_ko",
    "title_en",
    "summary_ko",
    "summary_en",
    "body_ko",
    "body_en",
)


async def write_report(update: Update, analysis_data: dict) -> dict:
    """Generate the final report using LLM based on analysis results.

    Args:
        update: The :class:`Update` being reported on.
        analysis_data: Dict returned by the analyser step.

    Returns:
        A dict with bilingual report fields, ``raw_response``, and optionally
        ``parse_error`` when the LLM output could not be parsed as JSON.
    """
    logger.info("Writing report for update %s – %s", update.id, update.title)
    start = time.monotonic()

    analysis_json = json.dumps(analysis_data, indent=2, ensure_ascii=False, default=str)

    user_message = WRITING_USER_TEMPLATE.format(
        analysis_json=analysis_json,
        title=update.title,
        published_date=update.published_date or "Unknown",
    )

    async with analysis_session(system_message=WRITING_SYSTEM_PROMPT) as session:
        raw_response = await send_message(session, user_message)

    elapsed = time.monotonic() - start
    logger.info("Report written in %.1fs (%d chars)", elapsed, len(raw_response))

    parsed = extract_json(raw_response)
    if parsed is None:
        logger.warning("Failed to parse report JSON for update %s", update.id)
        return {
            **{key: "" for key in _EXPECTED_KEYS},
            "raw_response": raw_response,
            "parse_error": "Could not extract valid JSON from model response",
        }

    result: dict = {key: parsed.get(key, "") for key in _EXPECTED_KEYS}
    result["raw_response"] = raw_response
    return result
