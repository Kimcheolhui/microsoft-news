"""HTML to clean text conversion for LLM input."""

from __future__ import annotations

from bs4 import BeautifulSoup


def html_to_text(html: str) -> str:
    """Convert HTML to clean text suitable for LLM consumption.

    Removes scripts, styles, navigation, and other non-content elements.
    """
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # Collapse multiple blank lines
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def truncate_for_llm(text: str, max_chars: int = 15000) -> str:
    """Truncate text to fit within LLM token limits."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[Content truncated]"
