"""Sequential pipeline runner for report generation."""

from __future__ import annotations

import logging
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any

from ingest.db.session import get_session
from ingest.models.update import Update

from analysis.models import Report, ReportRun
from analysis.config import AnalysisSettings

from .deep_scraper import scrape_full_content
from .researcher import find_related_context
from .analyzer import analyze_update
from .writer import write_report

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _record_step(
    report_id: uuid.UUID,
    step: str,
    status: str,
    started_at: datetime,
    *,
    input_data: dict | None = None,
    output_data: dict | None = None,
    error: dict | None = None,
    tokens_used: int | None = None,
) -> None:
    """Persist a :class:`ReportRun` row for one pipeline step."""
    with get_session() as session:
        run = ReportRun(
            report_id=report_id,
            step=step,
            status=status,
            started_at=started_at,
            finished_at=_now(),
            input_data=input_data,
            output_data=output_data,
            error=error,
            tokens_used=tokens_used,
        )
        session.add(run)


def _get_or_create_report(update_id: uuid.UUID) -> uuid.UUID:
    """Return the report ID for *update_id*, creating the row if needed."""
    with get_session() as session:
        report = (
            session.query(Report)
            .filter(Report.update_id == update_id)
            .first()
        )
        if report:
            report.status = "running"
            return report.id

        report = Report(update_id=update_id, status="running")
        session.add(report)
        session.flush()
        return report.id


def _save_report(
    report_id: uuid.UUID,
    *,
    scraped_content: dict[str, Any],
    research_data: dict[str, Any],
    analysis_data: dict[str, Any],
    report_content: dict[str, Any],
    model_used: str,
) -> None:
    """Persist final results on the :class:`Report` row."""
    with get_session() as session:
        report = session.get(Report, report_id)
        if report is None:
            logger.error("Report %s not found for saving", report_id)
            return

        report.status = "completed"
        report.update_type = analysis_data.get("update_type")
        report.affected_services = analysis_data.get("affected_services")
        report.title_ko = report_content.get("title_ko")
        report.title_en = report_content.get("title_en")
        report.summary_ko = report_content.get("summary_ko")
        report.summary_en = report_content.get("summary_en")
        report.body_ko = report_content.get("body_ko")
        report.body_en = report_content.get("body_en")
        report.analysis_data = analysis_data
        report.related_update_ids = [
            r["id"] for r in research_data.get("related_updates", [])
        ]
        report.scraped_content = scraped_content
        report.research_data = research_data
        report.model_used = model_used
        report.generated_at = _now()


def _fail_report(report_id: uuid.UUID, error_msg: str) -> None:
    """Mark the report as failed."""
    with get_session() as session:
        report = session.get(Report, report_id)
        if report:
            report.status = "failed"
            report.analysis_data = {"error": error_msg}


async def run_pipeline(update_id: str) -> dict[str, Any]:
    """Run the full analysis pipeline for a single update.

    Steps:
        1. deep_scraper  – fetch full article content
        2. researcher    – find related updates and docs
        3. analyzer      – LLM analysis of the content
        4. writer        – LLM report generation

    Args:
        update_id: UUID string of the update to process.

    Returns:
        A summary dict with ``status``, ``report_id``, and step results.
    """
    logger.info("Pipeline started for update %s", update_id)
    settings = AnalysisSettings.from_env()

    uid = uuid.UUID(update_id)

    # Load the update
    with get_session() as session:
        update = session.get(Update, uid)
        if update is None:
            raise ValueError(f"Update {update_id} not found")
        # Eagerly load attributes we need outside the session
        title = update.title
        source_url = update.source_url
        published_date = (
            update.published_date.isoformat() if update.published_date else None
        )

    report_id = _get_or_create_report(uid)
    logger.info("Report %s for update %s", report_id, update_id)

    result: dict[str, Any] = {"update_id": update_id, "report_id": str(report_id)}

    try:
        # ── Step 1: Deep scrape ──────────────────────────────────────
        step_start = _now()
        scraped_content = scrape_full_content(source_url)
        _record_step(
            report_id, "deep_scraper", "completed", step_start,
            input_data={"url": source_url},
            output_data={
                "raw_length": scraped_content.get("raw_length"),
                "truncated": scraped_content.get("truncated"),
                "error": scraped_content.get("error"),
            },
        )
        logger.info("Step 1 (deep_scraper) done")

        # ── Step 2: Research ─────────────────────────────────────────
        step_start = _now()
        with get_session() as session:
            update_obj = session.get(Update, uid)
            research_data = find_related_context(update_obj)
        _record_step(
            report_id, "researcher", "completed", step_start,
            output_data={"count": research_data.get("count")},
        )
        logger.info("Step 2 (researcher) done — %d related", research_data["count"])

        # ── Step 3: Analyze ──────────────────────────────────────────
        step_start = _now()
        with get_session() as session:
            update_obj = session.get(Update, uid)
            analysis_data = await analyze_update(
                update_obj, scraped_content, research_data,
            )
        _record_step(
            report_id, "analyzer", "completed", step_start,
            output_data={
                "update_type": analysis_data.get("update_type"),
                "affected_services": analysis_data.get("affected_services"),
            },
        )
        logger.info("Step 3 (analyzer) done — type=%s", analysis_data.get("update_type"))

        # ── Step 4: Write report ─────────────────────────────────────
        step_start = _now()
        with get_session() as session:
            update_obj = session.get(Update, uid)
            report_content = await write_report(update_obj, analysis_data)
        _record_step(
            report_id, "writer", "completed", step_start,
            output_data={k: bool(v) for k, v in report_content.items() if k != "raw_response"},
        )
        logger.info("Step 4 (writer) done")

        # ── Save final report ────────────────────────────────────────
        _save_report(
            report_id,
            scraped_content=scraped_content,
            research_data=research_data,
            analysis_data=analysis_data,
            report_content=report_content,
            model_used=settings.model,
        )

        result["status"] = "completed"
        result["update_type"] = analysis_data.get("update_type")
        result["title_ko"] = report_content.get("title_ko")
        result["title_en"] = report_content.get("title_en")

    except Exception as exc:
        logger.exception("Pipeline failed for update %s", update_id)
        _fail_report(report_id, str(exc))
        # Record the failed step
        _record_step(
            report_id, "pipeline", "failed", step_start,
            error={"message": str(exc), "traceback": traceback.format_exc()},
        )
        result["status"] = "failed"
        result["error"] = str(exc)

    logger.info("Pipeline finished for update %s — %s", update_id, result["status"])
    return result
