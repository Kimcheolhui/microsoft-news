"""Updates router."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import cast, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, joinedload

from api.deps import get_db
from api.schemas import UpdateDetailOut, UpdateListOut, UpdateSummaryOut
from ingest.models.source import Source
from ingest.models.update import Update

router = APIRouter(prefix="/updates", tags=["updates"])


@router.get("", response_model=UpdateListOut)
def list_updates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: str | None = Query(None, description="Comma-separated source names"),
    update_type: str | None = None,
    category: str | None = None,
    q: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
) -> UpdateListOut:
    stmt = select(Update)

    if source:
        source_names = [s.strip() for s in source.split(",") if s.strip()]
        stmt = stmt.join(Source, Update.source_id == Source.id).where(
            Source.name.in_(source_names)
        )
    if update_type:
        stmt = stmt.where(Update.update_type.contains(cast([update_type], JSONB)))
    if category:
        stmt = stmt.where(Update.categories.contains(cast([category], JSONB)))
    if q:
        stmt = stmt.where(
            Update.title.ilike(f"%{q}%") | Update.title_ko.ilike(f"%{q}%")
        )
    if date_from:
        stmt = stmt.where(Update.published_date >= date_from)
    if date_to:
        stmt = stmt.where(Update.published_date <= date_to)

    total = db.scalar(
        select(func.count()).select_from(stmt.subquery())
    )

    rows = (
        db.scalars(
            stmt.order_by(Update.published_date.desc().nullslast())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .all()
    )

    return UpdateListOut(
        items=[UpdateSummaryOut.model_validate(r) for r in rows],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/{update_id}", response_model=UpdateDetailOut)
def get_update(
    update_id: UUID,
    db: Session = Depends(get_db),
) -> UpdateDetailOut:
    row = db.scalars(
        select(Update)
        .options(joinedload(Update.report))
        .where(Update.id == update_id)
    ).first()

    if not row:
        raise HTTPException(status_code=404, detail="Update not found")

    return UpdateDetailOut.model_validate(row)
