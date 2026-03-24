"""Reports router."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from api.deps import get_db
from api.schemas import ReportDetailOut, ReportListOut, ReportOut, ReportRunOut
from analysis.models.report import Report
from ingest.models.update import Update

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=ReportListOut)
def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    update_type: str | None = None,
    db: Session = Depends(get_db),
) -> ReportListOut:
    stmt = select(Report)

    if status:
        stmt = stmt.where(Report.status == status)
    if update_type:
        stmt = stmt.where(Report.update_type == update_type)

    total = db.scalar(
        select(func.count()).select_from(stmt.subquery())
    )

    rows = (
        db.scalars(
            stmt.order_by(Report.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .all()
    )

    return ReportListOut(
        items=[ReportOut.model_validate(r) for r in rows],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/{report_id}", response_model=ReportDetailOut)
def get_report(
    report_id: UUID,
    db: Session = Depends(get_db),
) -> ReportDetailOut:
    row = db.scalars(
        select(Report)
        .options(joinedload(Report.runs), joinedload(Report.update))
        .where(Report.id == report_id)
    ).unique().first()

    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportDetailOut(
        **{
            k: v
            for k, v in ReportOut.model_validate(row).model_dump().items()
        },
        runs=[ReportRunOut.model_validate(r) for r in row.runs],
        update_title=row.update.title if row.update else None,
        update_source_url=row.update.source_url if row.update else None,
    )
