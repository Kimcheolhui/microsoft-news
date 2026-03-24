"""CLI entry point for the ingest pipeline."""

from __future__ import annotations

import logging
import sys

import click

from .scrapers import SCRAPERS

logger = logging.getLogger("ingest")


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging.")
def cli(verbose: bool):
    """Azure Updates ingestion pipeline."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        level=level,
        stream=sys.stderr,
    )


# ------------------------------------------------------------------
# scrape group
# ------------------------------------------------------------------


@cli.group()
def scrape():
    """Run scrapers to ingest updates."""


@scrape.command("run")
@click.option("--source", default=None, help="Scrape a specific source by name.")
@click.option("--all", "all_sources", is_flag=True, help="Scrape all enabled sources.")
@click.option("--dry-run", is_flag=True, help="Fetch data but don't write to DB.")
def scrape_run(source: str | None, all_sources: bool, dry_run: bool):
    """Scrape updates from one or all sources."""
    if dry_run:
        _scrape_dry_run(source, all_sources)
        return

    from .db.session import get_session
    from .engine import run_ingest
    from .models import Source

    if source:
        with get_session() as session:
            run = run_ingest(source, session)
            _print_run(run)
    elif all_sources:
        with get_session() as session:
            enabled = session.query(Source).filter_by(enabled=True).all()
            if not enabled:
                click.echo("No enabled sources found. Run 'ingest sources seed' first.")
                return
            for src in enabled:
                if src.name in SCRAPERS:
                    run = run_ingest(src.name, session)
                    _print_run(run)
                else:
                    click.echo(f"  ⏭  No scraper for '{src.name}', skipping")
    else:
        click.echo("Specify --source <name> or --all.")


def _scrape_dry_run(source: str | None, all_sources: bool):
    """Fetch and display scraped data without writing to the database."""
    from .scrapers import get_scraper

    names = []
    if source:
        names = [source]
    elif all_sources:
        names = list(SCRAPERS.keys())
    else:
        click.echo("Specify --source <name> or --all.")
        return

    for name in names:
        click.echo(f"\n── {name} ──")
        try:
            scraper = get_scraper(name)
        except KeyError as exc:
            click.echo(f"  ERROR: {exc}")
            continue

        items = scraper.scrape()
        click.echo(f"  Fetched {len(items)} items")
        for item in items[:5]:
            click.echo(f"  • {item.get('title', '?')[:80]}")
        if len(items) > 5:
            click.echo(f"  … and {len(items) - 5} more")


def _print_run(run):
    click.echo(
        f"  ✔ {run.source.name if run.source else '?'}: "
        f"status={run.status} found={run.items_found} "
        f"new={run.items_new} updated={run.items_updated}"
    )


# ------------------------------------------------------------------
# sources group
# ------------------------------------------------------------------


@cli.group()
def sources():
    """Manage ingest sources."""


@sources.command("list")
def sources_list():
    """List configured sources."""
    from .db.session import get_session
    from .models import Source

    with get_session() as session:
        rows = session.query(Source).order_by(Source.name).all()
        if not rows:
            click.echo("No sources configured. Run 'ingest sources seed'.")
            return

        header = f"{'Name':<25} {'Type':<8} {'Enabled':<9} {'Last Scraped':<22} URL"
        click.echo(header)
        click.echo("─" * len(header))
        for s in rows:
            scraped = str(s.last_scraped_at)[:19] if s.last_scraped_at else "never"
            click.echo(
                f"{s.name:<25} {s.source_type:<8} {'yes' if s.enabled else 'no':<9} "
                f"{scraped:<22} {s.url}"
            )


@sources.command("seed")
def sources_seed():
    """Populate default sources."""
    from .db.session import get_session
    from .seed import seed_sources

    with get_session() as session:
        created = seed_sources(session)
        click.echo(f"Seeded {created} new source(s).")


# ------------------------------------------------------------------
# runs command
# ------------------------------------------------------------------


@cli.command()
@click.option("--last", "last_n", default=10, help="Number of recent runs to show.")
def runs(last_n: int):
    """Show recent ingest runs."""
    from .db.session import get_session
    from .models import IngestRun

    with get_session() as session:
        rows = (
            session.query(IngestRun)
            .order_by(IngestRun.started_at.desc())
            .limit(last_n)
            .all()
        )
        if not rows:
            click.echo("No ingest runs recorded yet.")
            return

        header = (
            f"{'Started':<22} {'Source':<25} {'Status':<10} "
            f"{'Found':>6} {'New':>6} {'Updated':>8}"
        )
        click.echo(header)
        click.echo("─" * len(header))
        for r in rows:
            started = str(r.started_at)[:19] if r.started_at else "?"
            src_name = r.source.name if r.source else str(r.source_id)[:8]
            click.echo(
                f"{started:<22} {src_name:<25} {r.status:<10} "
                f"{r.items_found:>6} {r.items_new:>6} {r.items_updated:>8}"
            )


# ------------------------------------------------------------------
# health command
# ------------------------------------------------------------------


@cli.command()
def health():
    """Show health status for all ingest sources."""
    from .db.session import get_session
    from .utils.monitoring import get_health_summary

    with get_session() as session:
        summary = get_health_summary(session)

    if not summary:
        click.echo("No sources configured. Run 'ingest sources seed' first.")
        return

    header = (
        f"{'Source':<25} {'Status':<10} {'Last Run':<22} "
        f"{'Consecutive Failures':>21} {'Total Runs':>11}"
    )
    click.echo(header)
    click.echo("─" * len(header))
    for entry in summary:
        last_time = entry["last_run_time"][:19] if entry["last_run_time"] else "never"
        click.echo(
            f"{entry['name']:<25} {entry['last_run_status']:<10} {last_time:<22} "
            f"{entry['consecutive_failures']:>21} {entry['total_runs']:>11}"
        )


if __name__ == "__main__":
    cli()
