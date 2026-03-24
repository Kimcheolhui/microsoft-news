"""Update enrichment pipeline — classifies and translates updates via LLM."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from analysis.agents.client import analysis_session, send_message
from analysis.prompts.enrichment import ENRICHMENT_SYSTEM_PROMPT, build_enrichment_prompt
from analysis.utils.json_parser import extract_json
from ingest.enums import UPDATE_TYPES, CATEGORIES
from ingest.models.source import Source
from ingest.models.update import Update

logger = logging.getLogger(__name__)


def _validate_list(values: list | None, allowed: list[str]) -> list[str]:
    """Filter values to only those in the allowed set."""
    if not values or not isinstance(values, list):
        return []
    return [v for v in values if v in allowed]


async def enrich_update(session, update: Update, source_name: str) -> dict | None:
    """Enrich a single update via LLM. Returns parsed result or None on failure."""
    prompt = build_enrichment_prompt(
        title=update.title,
        summary=update.summary,
        source_name=source_name,
        published_date=str(update.published_date) if update.published_date else None,
    )

    try:
        response = await send_message(session, prompt)
        result = extract_json(response)
    except Exception:
        logger.exception("LLM enrichment failed for update %s", update.id)
        return None

    if not result:
        logger.warning("No JSON parsed from enrichment response for %s", update.id)
        return None

    return {
        "update_types": _validate_list(result.get("update_types"), UPDATE_TYPES),
        "categories": _validate_list(result.get("categories"), CATEGORIES),
        "services_affected": result.get("services_affected") or [],
        "title_ko": result.get("title_ko") or "",
        "summary_ko": result.get("summary_ko") or "",
    }


def apply_enrichment(db: Session, update: Update, data: dict) -> None:
    """Write enrichment results to the Update row."""
    update.update_type = data["update_types"]
    update.categories = data["categories"]
    update.services_affected = data["services_affected"]
    update.title_ko = data["title_ko"]
    update.summary_ko = data["summary_ko"]
    db.commit()
    logger.info("Enriched update %s: types=%s categories=%s",
                update.id, data["update_types"], data["categories"])


async def run_enrichment(
    db: Session,
    *,
    force: bool = False,
    limit: int | None = None,
    dry_run: bool = False,
) -> dict:
    """Enrich pending updates. Returns stats dict."""
    stmt = select(Update).join(Source)
    if not force:
        # Only updates without title_ko (not yet enriched)
        stmt = stmt.where(Update.title_ko.is_(None))
    stmt = stmt.order_by(Update.published_date.desc().nullslast())
    if limit:
        stmt = stmt.limit(limit)

    updates = db.execute(
        stmt.add_columns(Source.name)
    ).all()

    total = len(updates)
    if total == 0:
        logger.info("No updates to enrich")
        return {"total": 0, "enriched": 0, "failed": 0}

    logger.info("Enriching %d update(s) (force=%s, dry_run=%s)", total, force, dry_run)

    if dry_run:
        for upd, source_name in updates:
            print(f"  [DRY RUN] {upd.title[:80]}")
        return {"total": total, "enriched": 0, "failed": 0, "dry_run": True}

    enriched = 0
    failed = 0

    async with analysis_session(system_message=ENRICHMENT_SYSTEM_PROMPT) as llm_session:
        for upd, source_name in updates:
            result = await enrich_update(llm_session, upd, source_name)
            if result:
                apply_enrichment(db, upd, result)
                enriched += 1
            else:
                failed += 1

    return {"total": total, "enriched": enriched, "failed": failed}
