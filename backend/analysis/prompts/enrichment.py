"""Prompts for the update enrichment pipeline."""

from __future__ import annotations

from ingest.enums import UPDATE_TYPES, CATEGORIES

_UPDATE_TYPE_LIST = ", ".join(UPDATE_TYPES)
_CATEGORY_LIST = ", ".join(CATEGORIES)

ENRICHMENT_SYSTEM_PROMPT = """\
You are an Azure cloud services analyst. Your job is to classify and translate \
Azure ecosystem updates. You must return a JSON object — no markdown, no extra text.

Classification rules:
- update_types and categories are LISTS (multi-select). Pick ALL that apply.
- services_affected is a list of specific Azure service names mentioned.
- Translate title and summary to natural, professional Korean."""

ENRICHMENT_USER_TEMPLATE = """\
Classify and translate the following update.

Title: {title}
Summary: {summary}
Source: {source_name}
Published: {published_date}

Return ONLY a JSON object with these fields:
{{
  "update_types": [<one or more from: {update_types}>],
  "categories": [<one or more from: {categories}>],
  "services_affected": [<list of Azure service names>],
  "title_ko": "<Korean translation of the title>",
  "summary_ko": "<Korean translation of the summary>"
}}"""


def build_enrichment_prompt(
    title: str,
    summary: str | None,
    source_name: str,
    published_date: str | None,
) -> str:
    return ENRICHMENT_USER_TEMPLATE.format(
        title=title,
        summary=summary or "(no summary)",
        source_name=source_name,
        published_date=published_date or "unknown",
        update_types=_UPDATE_TYPE_LIST,
        categories=_CATEGORY_LIST,
    )
