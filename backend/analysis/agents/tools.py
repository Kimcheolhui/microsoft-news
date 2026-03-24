"""Custom tools for the analysis agent (DB query, web scrape)."""

from __future__ import annotations


async def query_related_updates(search_term: str, limit: int = 10) -> str:
    """Query the updates table for related content."""
    from ingest.db.session import get_session
    from ingest.models import Update

    with get_session() as session:
        updates = (
            session.query(Update)
            .filter(Update.title.ilike(f"%{search_term}%"))
            .limit(limit)
            .all()
        )
        if not updates:
            return "No related updates found."
        results = []
        for u in updates:
            results.append(
                f"- [{u.title}]({u.source_url}) ({u.published_date})"
            )
        return "\n".join(results)


async def scrape_url(url: str) -> str:
    """Fetch a URL and extract text content."""
    import requests
    from bs4 import BeautifulSoup

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:15000] if len(text) > 15000 else text
    except Exception as e:
        return f"Error scraping {url}: {e}"
