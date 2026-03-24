"""Database session dependency for FastAPI."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from ingest.db.session import get_session_factory


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
