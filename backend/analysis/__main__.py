"""CLI entry point for the analysis pipeline."""

from __future__ import annotations

import logging
import sys

import click

logger = logging.getLogger("analysis")


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging.")
def cli(verbose: bool):
    """Azure Updates analysis pipeline."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        level=level,
        stream=sys.stderr,
    )


@cli.group()
def generate():
    """Generate analysis reports."""


@generate.command("update")
@click.argument("update_id")
def generate_update(update_id: str):
    """Generate a report for a single update by ID."""
    import asyncio

    from .pipeline.orchestrator import run_pipeline

    click.echo(f"Generating report for update {update_id}...")
    try:
        report = asyncio.run(run_pipeline(update_id))
        click.echo(
            f"✅ Report {report.status}: "
            f"{report.title_en or report.title_ko or 'N/A'}"
        )
    except ValueError as e:
        click.echo(f"❌ {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"❌ Pipeline failed: {e}", err=True)
        raise SystemExit(1)


@generate.command("pending")
@click.option("--dry-run", is_flag=True, help="Show what would be processed without running.")
def generate_pending(dry_run: bool):
    """Generate reports for all updates without reports."""
    import asyncio

    from ingest.db.session import get_session
    from ingest.models import Update

    from .models import Report
    from .pipeline.orchestrator import run_pipeline

    with get_session() as session:
        existing_ids = {
            r.update_id for r in session.query(Report.update_id).all()
        }
        query = session.query(Update)
        if existing_ids:
            query = query.filter(~Update.id.in_(existing_ids))
        updates = [(u.id, u.title) for u in query.all()]

    click.echo(f"Found {len(updates)} updates to process.")

    if not updates:
        return

    if dry_run:
        for uid, title in updates:
            click.echo(f"  Would process: {title} ({uid})")
        return

    completed = failed = skipped = 0
    for i, (uid, title) in enumerate(updates, 1):
        click.echo(f"[{i}/{len(updates)}] Processing: {title}...")
        try:
            report = asyncio.run(run_pipeline(uid))
            if report.status == "completed":
                click.echo("  ✅ Completed")
                completed += 1
            else:
                click.echo(f"  ❌ Failed: {report.status}")
                failed += 1
        except Exception as e:
            click.echo(f"  ❌ Failed: {e}")
            failed += 1

    click.echo(f"\nDone: {completed} completed, {failed} failed, {skipped} skipped")


@generate.command("all")
@click.option("--force", is_flag=True, help="Regenerate even completed reports.")
def generate_all(force: bool):
    """Regenerate reports for all updates."""
    import asyncio

    from ingest.db.session import get_session
    from ingest.models import Update

    from .models import Report
    from .pipeline.orchestrator import run_pipeline

    with get_session() as session:
        if force:
            # Reset completed reports so the pipeline reprocesses them
            session.query(Report).filter(
                Report.status == "completed",
            ).update({"status": "pending"})
            updates = [(u.id, u.title) for u in session.query(Update).all()]
        else:
            completed_ids = {
                r.update_id
                for r in session.query(Report.update_id)
                .filter(Report.status == "completed")
                .all()
            }
            query = session.query(Update)
            if completed_ids:
                query = query.filter(~Update.id.in_(completed_ids))
            updates = [(u.id, u.title) for u in query.all()]

    click.echo(f"Found {len(updates)} updates to process.")

    if not updates:
        return

    completed = failed = skipped = 0
    for i, (uid, title) in enumerate(updates, 1):
        click.echo(f"[{i}/{len(updates)}] Processing: {title}...")
        try:
            report = asyncio.run(run_pipeline(uid))
            if report.status == "completed":
                click.echo("  ✅ Completed")
                completed += 1
            else:
                click.echo(f"  ❌ Failed: {report.status}")
                failed += 1
        except Exception as e:
            click.echo(f"  ❌ Failed: {e}")
            failed += 1

    click.echo(f"\nDone: {completed} completed, {failed} failed, {skipped} skipped")


@cli.group()
def enrich():
    """Enrich updates with classification and Korean translation."""


@enrich.command("pending")
@click.option("--limit", type=int, default=None, help="Max updates to process.")
@click.option("--dry-run", is_flag=True, help="Show what would be processed.")
def enrich_pending(limit: int | None, dry_run: bool):
    """Enrich updates that haven't been classified yet."""
    import asyncio

    from ingest.db.session import get_session
    from .pipeline.enrichment import run_enrichment

    with get_session() as session:
        result = asyncio.run(run_enrichment(session, limit=limit, dry_run=dry_run))

    click.echo(f"Total: {result['total']}, Enriched: {result['enriched']}, Failed: {result['failed']}")


@enrich.command("all")
@click.option("--force", is_flag=True, help="Re-enrich already classified updates.")
@click.option("--limit", type=int, default=None, help="Max updates to process.")
def enrich_all(force: bool, limit: int | None):
    """Enrich all updates (use --force to re-classify)."""
    import asyncio

    from ingest.db.session import get_session
    from .pipeline.enrichment import run_enrichment

    with get_session() as session:
        result = asyncio.run(run_enrichment(session, force=force, limit=limit))

    click.echo(f"Total: {result['total']}, Enriched: {result['enriched']}, Failed: {result['failed']}")


@cli.command()
def status():
    """Show report generation status."""
    from sqlalchemy import func as sqlfunc

    from ingest.db.session import get_session

    from .models import Report

    with get_session() as session:
        total = session.query(Report).count()
        if total == 0:
            click.echo("No reports generated yet.")
            return

        status_counts = (
            session.query(Report.status, sqlfunc.count(Report.id))
            .group_by(Report.status)
            .all()
        )

        click.echo(f"Total reports: {total}")
        click.echo("─" * 30)
        for s, count in sorted(status_counts, key=lambda x: x[0]):
            click.echo(f"  {s:<15} {count:>5}")


if __name__ == "__main__":
    cli()
