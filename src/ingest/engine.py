"""Core ingest orchestration engine."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .models import Source, Update, IngestRun
from .scrapers import get_scraper
from .utils.dedup import find_existing_urls

logger = logging.getLogger(__name__)


def run_ingest(source_name: str, session: Session) -> IngestRun:
    """Run ingest for a single source.

    Creates an IngestRun record, invokes the scraper, upserts updates,
    and returns the completed IngestRun.
    """
    # 1. Look up or create Source
    source = session.query(Source).filter_by(name=source_name).first()
    if source is None:
        raise ValueError(f"Unknown source: {source_name!r}. Run 'ingest sources seed' first.")

    # 2. Create IngestRun
    run = IngestRun(
        id=uuid.uuid4(),
        source_id=source.id,
        started_at=datetime.now(timezone.utc),
        status="running",
    )
    session.add(run)
    session.flush()

    try:
        # 3. Invoke scraper
        scraper = get_scraper(source_name)
        items = scraper.scrape()
        run.items_found = len(items)

        # 4. Dedup and upsert
        urls = [item["source_url"] for item in items if item.get("source_url")]
        existing_urls = find_existing_urls(session, urls)

        items_new = 0
        items_updated = 0

        for item in items:
            url = item.get("source_url")
            if not url:
                continue

            if url in existing_urls:
                # Update existing record
                existing = session.query(Update).filter_by(source_url=url).first()
                if existing:
                    for field in ("title", "summary", "published_date", "categories", "raw_data"):
                        if item.get(field) is not None:
                            setattr(existing, field, item[field])
                    items_updated += 1
            else:
                update = Update(
                    id=uuid.uuid4(),
                    source_id=source.id,
                    title=item["title"],
                    summary=item.get("summary"),
                    source_url=url,
                    published_date=item.get("published_date"),
                    categories=item.get("categories"),
                    raw_data=item.get("raw_data"),
                )
                session.add(update)
                items_new += 1

        # 5. Finalize run
        run.items_new = items_new
        run.items_updated = items_updated
        run.status = "success"
        run.finished_at = datetime.now(timezone.utc)

        # 6. Update source timestamp
        source.last_scraped_at = datetime.now(timezone.utc)

        session.flush()
        logger.info(
            "Ingest complete for %s: found=%d new=%d updated=%d",
            source_name,
            run.items_found,
            items_new,
            items_updated,
        )

    except Exception as exc:
        logger.exception("Ingest failed for %s", source_name)
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        run.errors = {"error": str(exc)}
        session.flush()

    return run
