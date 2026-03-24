"""Extract JSON objects from LLM responses."""

from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)


def extract_json(text: str) -> dict | None:
    """Extract a JSON object from text that may contain markdown fences or extra text.

    Tries three strategies in order:

    1. Parse the entire string as JSON.
    2. Look for a fenced ``\u0060\u0060\u0060json ... \u0060\u0060\u0060`` block and parse its content.
    3. Locate the first ``{`` and last ``}`` and attempt to parse the slice.

    Returns:
        The parsed ``dict``, or ``None`` if all attempts fail.
    """
    if not text:
        return None

    # 1. Direct parse
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except (json.JSONDecodeError, TypeError):
        pass

    # 2. Fenced code block
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group(1))
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, TypeError):
            pass

    # 3. First '{' to last '}'
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        try:
            result = json.loads(text[first : last + 1])
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, TypeError):
            pass

    logger.warning("Failed to extract JSON from response (%d chars)", len(text))
    return None
