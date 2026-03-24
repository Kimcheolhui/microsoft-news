from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ingest.models.base import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    update_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("updates.id"), unique=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default=text("'pending'")
    )
    update_type: Mapped[str | None] = mapped_column(String, nullable=True)
    affected_services: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    title_ko: Mapped[str | None] = mapped_column(String, nullable=True)
    title_en: Mapped[str | None] = mapped_column(String, nullable=True)
    summary_ko: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_ko: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    related_update_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    references: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scraped_content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    research_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    update: Mapped["Update"] = relationship(back_populates="report")  # noqa: F821
    runs: Mapped[list["ReportRun"]] = relationship(back_populates="report")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Report update_id={self.update_id!r} status={self.status!r}>"
