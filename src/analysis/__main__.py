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
        result = asyncio.run(run_pipeline(update_id))
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if result["status"] == "completed":
        click.echo(f"✓ Report generated (ID: {result['report_id']})")
        if result.get("title_en"):
            click.echo(f"  EN: {result['title_en']}")
        if result.get("title_ko"):
            click.echo(f"  KO: {result['title_ko']}")
    else:
        click.echo(f"✗ Pipeline failed: {result.get('error')}", err=True)
        raise SystemExit(1)


@generate.command("pending")
def generate_pending():
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
        pending = (
            session.query(Update)
            .filter(~Update.id.in_(existing_ids))
            .order_by(Update.published_date.desc().nullslast())
            .all()
        )
        pending_ids = [(str(u.id), u.title) for u in pending]

    if not pending_ids:
        click.echo("No pending updates — all reports are up to date.")
        return

    click.echo(f"Found {len(pending_ids)} updates without reports.")
    completed = 0
    failed = 0

    for uid, title in pending_ids:
        click.echo(f"  Processing: {title[:80]}...")
        try:
            result = asyncio.run(run_pipeline(uid))
            if result["status"] == "completed":
                completed += 1
                click.echo(f"    ✓ Done")
            else:
                failed += 1
                click.echo(f"    ✗ Failed: {result.get('error', 'unknown')}")
        except Exception as exc:
            failed += 1
            click.echo(f"    ✗ Error: {exc}")

    click.echo(f"\nCompleted: {completed}, Failed: {failed}, Total: {len(pending_ids)}")


@generate.command("all")
def generate_all():
    """Regenerate reports for all updates."""
    import asyncio

    from ingest.db.session import get_session
    from ingest.models import Update

    from .pipeline.orchestrator import run_pipeline

    with get_session() as session:
        updates = (
            session.query(Update)
            .order_by(Update.published_date.desc().nullslast())
            .all()
        )
        all_ids = [(str(u.id), u.title) for u in updates]

    if not all_ids:
        click.echo("No updates found in the database.")
        return

    click.echo(f"Regenerating reports for {len(all_ids)} updates...")
    completed = 0
    failed = 0

    for uid, title in all_ids:
        click.echo(f"  Processing: {title[:80]}...")
        try:
            result = asyncio.run(run_pipeline(uid))
            if result["status"] == "completed":
                completed += 1
                click.echo(f"    ✓ Done")
            else:
                failed += 1
                click.echo(f"    ✗ Failed: {result.get('error', 'unknown')}")
        except Exception as exc:
            failed += 1
            click.echo(f"    ✗ Error: {exc}")

    click.echo(f"\nCompleted: {completed}, Failed: {failed}, Total: {len(all_ids)}")


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
