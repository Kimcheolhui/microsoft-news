"""Tests for the FastAPI API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import JSON, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.app import app
from api.deps import get_db
from ingest.models.base import Base
from ingest.models.source import Source
from ingest.models.update import Update
from analysis.models.report import Report
from analysis.models.report_run import ReportRun

# Patch JSONB columns to JSON and remove PG-specific server defaults for SQLite
for table in Base.metadata.tables.values():
    for column in table.columns:
        if isinstance(column.type, JSONB):
            column.type = JSON()
        if column.server_default is not None:
            column.server_default = None
        if column.server_onupdate is not None:
            column.server_onupdate = None

# In-memory SQLite with shared connection
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=engine, expire_on_commit=False)


def override_get_db():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


def _make_source(db: Session, **kwargs) -> Source:
    now = datetime.now(timezone.utc)
    src = Source(
        id=kwargs.get("id", uuid.uuid4()),
        name=kwargs.get("name", "test-source"),
        url=kwargs.get("url", "https://example.com/feed"),
        source_type=kwargs.get("source_type", "rss"),
        created_at=kwargs.get("created_at", now),
        updated_at=kwargs.get("updated_at", now),
    )
    db.add(src)
    db.commit()
    db.refresh(src)
    return src


def _make_update(db: Session, source: Source, **kwargs) -> Update:
    now = datetime.now(timezone.utc)
    upd = Update(
        id=kwargs.get("id", uuid.uuid4()),
        source_id=source.id,
        title=kwargs.get("title", "Test Update"),
        summary=kwargs.get("summary", "A test summary"),
        source_url=kwargs.get("source_url", f"https://example.com/{uuid.uuid4()}"),
        published_date=kwargs.get("published_date", now),
        update_type=kwargs.get("update_type"),
        ingested_at=kwargs.get("ingested_at", now),
        created_at=kwargs.get("created_at", now),
    )
    db.add(upd)
    db.commit()
    db.refresh(upd)
    return upd


def _make_report(db: Session, update: Update, **kwargs) -> Report:
    now = datetime.now(timezone.utc)
    rpt = Report(
        id=kwargs.get("id", uuid.uuid4()),
        update_id=update.id,
        status=kwargs.get("status", "completed"),
        title_ko=kwargs.get("title_ko", "테스트 제목"),
        title_en=kwargs.get("title_en", "Test Title"),
        summary_ko=kwargs.get("summary_ko", "요약"),
        summary_en=kwargs.get("summary_en", "Summary"),
        body_ko=kwargs.get("body_ko", "본문"),
        body_en=kwargs.get("body_en", "Body"),
        generated_at=kwargs.get("generated_at", now),
        created_at=kwargs.get("created_at", now),
        updated_at=kwargs.get("updated_at", now),
    )
    db.add(rpt)
    db.commit()
    db.refresh(rpt)
    return rpt


# --- Health ---


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# --- Sources ---


def test_list_sources_empty():
    resp = client.get("/api/v1/sources")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_sources():
    db = TestSession()
    _make_source(db, name="azure-blog")
    _make_source(db, name="github-blog")
    db.close()

    resp = client.get("/api/v1/sources")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["name"] == "azure-blog"
    assert data[1]["name"] == "github-blog"


# --- Updates ---


def test_list_updates_empty():
    resp = client.get("/api/v1/updates")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_updates_pagination():
    db = TestSession()
    src = _make_source(db)
    for i in range(5):
        _make_update(db, src, title=f"Update {i}")
    db.close()

    resp = client.get("/api/v1/updates?page=1&page_size=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2


def test_list_updates_filter_by_source():
    db = TestSession()
    src1 = _make_source(db, name="src-a")
    src2 = _make_source(db, name="src-b")
    _make_update(db, src1, title="From A")
    _make_update(db, src2, title="From B")
    db.close()

    resp = client.get("/api/v1/updates?source=src-a")
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "From A"


def test_list_updates_search():
    db = TestSession()
    src = _make_source(db)
    _make_update(db, src, title="Azure Kubernetes Update")
    _make_update(db, src, title="GitHub Actions Release")
    db.close()

    resp = client.get("/api/v1/updates?q=kubernetes")
    data = resp.json()
    assert data["total"] == 1
    assert "Kubernetes" in data["items"][0]["title"]


def test_get_update_detail():
    db = TestSession()
    src = _make_source(db)
    upd = _make_update(db, src, title="Detail Test")
    db.close()

    resp = client.get(f"/api/v1/updates/{upd.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Detail Test"


def test_get_update_not_found():
    resp = client.get(f"/api/v1/updates/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_get_update_with_report():
    db = TestSession()
    src = _make_source(db)
    upd = _make_update(db, src)
    _make_report(db, upd, title_en="Report Title")
    db.close()

    resp = client.get(f"/api/v1/updates/{upd.id}")
    data = resp.json()
    assert data["report"] is not None
    assert data["report"]["title_en"] == "Report Title"


# --- Reports ---


def test_list_reports_empty():
    resp = client.get("/api/v1/reports")
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_reports():
    db = TestSession()
    src = _make_source(db)
    upd = _make_update(db, src)
    _make_report(db, upd)
    db.close()

    resp = client.get("/api/v1/reports")
    data = resp.json()
    assert data["total"] == 1


def test_list_reports_filter_by_status():
    db = TestSession()
    src = _make_source(db)
    upd1 = _make_update(db, src, source_url="https://a.com/1")
    upd2 = _make_update(db, src, source_url="https://a.com/2")
    _make_report(db, upd1, status="completed")
    _make_report(db, upd2, status="pending")
    db.close()

    resp = client.get("/api/v1/reports?status=completed")
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "completed"


def test_get_report_detail():
    db = TestSession()
    src = _make_source(db)
    upd = _make_update(db, src, title="My Update")
    rpt = _make_report(db, upd, title_ko="한국어 제목")
    db.close()

    resp = client.get(f"/api/v1/reports/{rpt.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["title_ko"] == "한국어 제목"
    assert data["update_title"] == "My Update"
    assert data["runs"] == []


def test_get_report_not_found():
    resp = client.get(f"/api/v1/reports/{uuid.uuid4()}")
    assert resp.status_code == 404


# --- Stats ---


def test_stats_empty():
    resp = client.get("/api/v1/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_updates"] == 0
    assert data["total_reports"] == 0


def test_stats_with_data():
    db = TestSession()
    src = _make_source(db, name="azure")
    upd = _make_update(db, src)
    _make_report(db, upd, status="completed")
    db.close()

    resp = client.get("/api/v1/stats")
    data = resp.json()
    assert data["total_updates"] == 1
    assert data["total_reports"] == 1
    assert data["reports_by_status"]["completed"] == 1
    assert len(data["sources"]) == 1
    assert data["sources"][0]["source_name"] == "azure"
    assert data["sources"][0]["update_count"] == 1
