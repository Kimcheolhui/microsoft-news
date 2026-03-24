# Azure News

Data ingestion pipeline that scrapes Azure-ecosystem updates from multiple sources and stores them in PostgreSQL.

**Sources:** Azure Updates (RSS), Azure Blog, Fabric Blog, GitHub Blog

## Quick Start

```bash
# Install
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your DATABASE_URL

# Seed sources and run
python -m ingest sources seed
python -m ingest scrape run --all
```

## CLI Commands

| Command | Description |
|---|---|
| `python -m ingest scrape run --all` | Scrape all enabled sources |
| `python -m ingest scrape run --source azure-blog` | Scrape a single source |
| `python -m ingest scrape run --dry-run --all` | Dry run (no DB writes) |
| `python -m ingest sources seed` | Seed default sources (idempotent) |
| `python -m ingest sources list` | List configured sources |
| `python -m ingest runs --last 4` | Show recent ingest runs |

## Scheduling

Automated ingestion runs via GitHub Actions:

- **Twice daily** at 06:00 UTC and 18:00 UTC (`.github/workflows/ingest-schedule.yml`)
- **Manual trigger** from the Actions tab with source selection and dry-run option (`.github/workflows/ingest-manual.yml`)

### Triggering a Manual Run

1. Go to **Actions → Manual Ingest → Run workflow**
2. Select a source (or "all") and optionally enable dry run
3. Click **Run workflow**

### Required Secrets

| Secret | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |

## Development

```bash
pip install -e ".[dev]"
pytest
```
