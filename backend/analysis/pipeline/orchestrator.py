"""Sequential pipeline runner for report generation."""

from __future__ import annotations

import logging
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any

from ingest.db.session import get_session
from ingest.models.update import Update

from analysis.config import AnalysisSettings
from analysis.models import Report, ReportRun

from .deep_scraper import scrape_full_content
from .researcher import find_related_context
from .analyzer import analyze_update
from .writer import write_report

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _run_step(
    report_id: uuid.UUID,
    step: str,
    func: Any,
    *args: Any,
    is_async: bool = False,
) -> dict[str, Any]:
    """Execute one pipeline step and persist a :class:`ReportRun` record.

    Creates a ReportRun with status='running' before calling *func*, then
    updates it to 'completed' or 'failed' depending on the outcome.
    """
    started_at = _now()

    with get_session() as session:
        run = ReportRun(
            report_id=report_id,
            step=step,
            status="running",
            started_at=started_at,
        )
        session.add(run)
        session.flush()
        run_id = run.id

    try:
        result = (await func(*args)) if is_async else func(*args)

        with get_session() as session:
            run = session.get(ReportRun, run_id)
            run.status = "completed"
            run.finished_at = _now()
            run.output_data = result

        return result

    except Exception as exc:
        with get_session() as session:
            run = session.get(ReportRun, run_id)
            run.status = "failed"
            run.finished_at = _now()
            run.error = {
                "message": str(exc),
                "traceback": traceback.format_exc(),
            }
        raise


def _set_report_status(report_id: uuid.UUID, status: str) -> None:
    """Update the status column on a :class:`Report`."""
    with get_session() as session:
        report = session.get(Report, report_id)
        if report:
            report.status = status


async def run_pipeline(update_id: str | uuid.UUID) -> Report:
    """Run the full analysis pipeline for a single update.

    Steps:
        1. deep_scraper  – fetch full article content
        2. researcher    – find related updates and docs
        3. analyzer      – LLM analysis of the content
        4. writer        – LLM report generation

    Args:
        update_id: UUID (string or object) of the update to process.

    Returns:
        The :class:`Report` row (detached from session).

    Raises:
        ValueError: If the update does not exist.
    """
    logger.info("Pipeline started for update %s", update_id)
    uid = uuid.UUID(str(update_id))

    # ── 1. Load the Update ──────────────────────────────────────────
    with get_session() as session:
        update = session.get(Update, uid)
        if update is None:
            raise ValueError(f"Update {update_id} not found")
        # Force-load scalar attributes so they stay available after
        # the session closes (expire_on_commit=False handles caching).
        _ = (
            update.id, update.title, update.summary, update.body,
            update.source_url, update.published_date,
        )

    # ── 2. Create or get existing Report ────────────────────────────
    with get_session() as session:
        report = (
            session.query(Report)
            .filter(Report.update_id == uid)
            .first()
        )
        if report is not None:
            if report.status == "completed":
                logger.info(
                    "Report already completed for update %s, skipping",
                    update_id,
                )
                return report
            # Reset failed / pending / stale-processing for retry
            report.status = "pending"
            report_id = report.id
        else:
            report = Report(update_id=uid, status="pending")
            session.add(report)
            session.flush()
            report_id = report.id

    # ── 3. Mark processing ──────────────────────────────────────────
    _set_report_status(report_id, "processing")
    logger.info("Report %s processing for update %s", report_id, update_id)

    scraped_content: dict[str, Any] = {}
    research_data: dict[str, Any] = {}

    # ── Step 1: deep_scraper (sync – continue on error) ─────────────
    logger.info("Step 1/4: deep_scraper for update %s", update_id)
    try:
        scraped_content = await _run_step(
            report_id, "deep_scraper", scrape_full_content, update.source_url,
        )
        with get_session() as session:
            rpt = session.get(Report, report_id)
            rpt.scraped_content = scraped_content
    except Exception as exc:
        logger.warning("deep_scraper failed, continuing: %s", exc)
        scraped_content = {"url": update.source_url, "error": str(exc), "text": ""}

    # ── Step 2: researcher (sync – continue on error) ───────────────
    logger.info("Step 2/4: researcher for update %s", update_id)
    try:
        research_data = await _run_step(
            report_id, "researcher", find_related_context, update,
        )
        with get_session() as session:
            rpt = session.get(Report, report_id)
            rpt.research_data = research_data
    except Exception as exc:
        logger.warning("researcher failed, continuing: %s", exc)
        research_data = {"keywords": [], "related_updates": [], "count": 0}

    # ── Step 3: analyzer (async – STOP pipeline on error) ───────────
    logger.info("Step 3/4: analyzer for update %s", update_id)
    try:
        analysis_data = await _run_step(
            report_id, "analyzer", analyze_update,
            update, scraped_content, research_data,
            is_async=True,
        )
        with get_session() as session:
            rpt = session.get(Report, report_id)
            rpt.analysis_data = analysis_data
            rpt.update_type = analysis_data.get("update_type")
            rpt.affected_services = analysis_data.get("affected_services")
    except Exception as exc:
        logger.error("analyzer failed, stopping pipeline: %s", exc)
        _set_report_status(report_id, "failed")
        with get_session() as session:
            report = session.get(Report, report_id)
        logger.info(
            "Pipeline finished for update %s — %s", update_id, report.status,
        )
        return report

    # ── Step 4: writer (async – fail report on error) ───────────────
    logger.info("Step 4/4: writer for update %s", update_id)
    try:
        report_content = await _run_step(
            report_id, "writer", write_report, update, analysis_data,
            is_async=True,
        )
        with get_session() as session:
            rpt = session.get(Report, report_id)
            rpt.title_ko = report_content.get("title_ko")
            rpt.title_en = report_content.get("title_en")
            rpt.summary_ko = report_content.get("summary_ko")
            rpt.summary_en = report_content.get("summary_en")
            rpt.body_ko = report_content.get("body_ko")
            rpt.body_en = report_content.get("body_en")
            rpt.related_update_ids = [
                r["id"] for r in research_data.get("related_updates", [])
            ]
            rpt.model_used = AnalysisSettings.from_env().model
            rpt.generated_at = _now()
            rpt.status = "completed"
    except Exception as exc:
        logger.error("writer failed: %s", exc)
        _set_report_status(report_id, "failed")

    # ── Return final report ─────────────────────────────────────────
    with get_session() as session:
        report = session.get(Report, report_id)

    logger.info(
        "Pipeline finished for update %s — %s", update_id, report.status,
    )
    return report


async def run_pipeline_batch(
    update_ids: list[str | uuid.UUID],
) -> list[Report]:
    """Run the pipeline for multiple updates sequentially."""
    results: list[Report] = []
    for update_id in update_ids:
        try:
            report = await run_pipeline(update_id)
            results.append(report)
        except Exception as exc:
            logger.error("Pipeline failed for update %s: %s", update_id, exc)
    return results
