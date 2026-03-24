"""Sources router."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import SourceOut
from ingest.models.source import Source

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)) -> list[SourceOut]:
    rows = db.scalars(
        select(Source).order_by(Source.name)
    ).all()
    return [SourceOut.model_validate(r) for r in rows]
