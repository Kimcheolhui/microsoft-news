"""Pydantic response schemas for the API."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# --- Source ---


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    url: str
    source_type: str
    enabled: bool
    last_scraped_at: datetime | None = None
    created_at: datetime


# --- Update ---


class UpdateSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    title: str
    title_ko: str | None = None
    summary: str | None = None
    summary_ko: str | None = None
    source_url: str
    published_date: datetime | None = None
    update_type: list[str] | None = None
    categories: list[str] | None = None
    services_affected: list[str] | None = None
    ingested_at: datetime


class ReportBriefOut(BaseModel):
    """Minimal report info embedded in update detail."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    update_type: str | None = None
    title_ko: str | None = None
    title_en: str | None = None
    summary_ko: str | None = None
    summary_en: str | None = None
    generated_at: datetime | None = None


class UpdateDetailOut(UpdateSummaryOut):
    body: str | None = None
    raw_data: dict | None = None
    report: ReportBriefOut | None = None


class UpdateListOut(BaseModel):
    items: list[UpdateSummaryOut]
    total: int
    page: int
    page_size: int


# --- Report ---


class ReportRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    step: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    error: dict | None = None
    tokens_used: int | None = None


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    update_id: UUID
    status: str
    update_type: str | None = None
    affected_services: dict | list | None = None
    title_ko: str | None = None
    title_en: str | None = None
    summary_ko: str | None = None
    summary_en: str | None = None
    body_ko: str | None = None
    body_en: str | None = None
    analysis_data: dict | None = None
    related_update_ids: dict | list | None = None
    references: dict | list | None = None
    model_used: str | None = None
    tokens_used: int | None = None
    generated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ReportDetailOut(ReportOut):
    runs: list[ReportRunOut] = []
    update_title: str | None = None
    update_source_url: str | None = None


class ReportListOut(BaseModel):
    items: list[ReportOut]
    total: int
    page: int
    page_size: int


# --- Stats ---


class SourceStatsOut(BaseModel):
    source_name: str
    update_count: int
    last_scraped_at: datetime | None = None


class StatsOut(BaseModel):
    total_updates: int
    total_reports: int
    reports_by_status: dict[str, int]
    sources: list[SourceStatsOut]
