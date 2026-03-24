from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class IngestRun(Base):
    __tablename__ = "ingest_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    items_found: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    items_new: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    items_updated: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    errors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    source: Mapped["Source"] = relationship(back_populates="ingest_runs")  # noqa: F821

    def __repr__(self) -> str:
        return f"<IngestRun source_id={self.source_id!r} status={self.status!r}>"
