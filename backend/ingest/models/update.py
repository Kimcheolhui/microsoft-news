from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Update(Base):
    __tablename__ = "updates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    published_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    categories: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    services_affected: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    update_type: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    source: Mapped["Source"] = relationship(back_populates="updates")  # noqa: F821
    report: Mapped["Report"] = relationship(back_populates="update")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Update title={self.title!r}>"
