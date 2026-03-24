"""Stats router."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import SourceStatsOut, StatsOut
from analysis.models.report import Report
from ingest.models.source import Source
from ingest.models.update import Update

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)) -> StatsOut:
    total_updates = db.scalar(select(func.count(Update.id))) or 0
    total_reports = db.scalar(select(func.count(Report.id))) or 0

    # Reports grouped by status
    status_rows = db.execute(
        select(Report.status, func.count(Report.id)).group_by(Report.status)
    ).all()
    reports_by_status = {row[0]: row[1] for row in status_rows}

    # Per-source update counts
    source_rows = db.execute(
        select(
            Source.name,
            func.count(Update.id),
            Source.last_scraped_at,
        )
        .outerjoin(Update, Source.id == Update.source_id)
        .group_by(Source.id, Source.name, Source.last_scraped_at)
        .order_by(Source.name)
    ).all()

    sources = [
        SourceStatsOut(
            source_name=row[0],
            update_count=row[1],
            last_scraped_at=row[2],
        )
        for row in source_rows
    ]

    return StatsOut(
        total_updates=total_updates,
        total_reports=total_reports,
        reports_by_status=reports_by_status,
        sources=sources,
    )
