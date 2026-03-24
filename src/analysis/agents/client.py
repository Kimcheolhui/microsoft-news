"""Copilot SDK client wrapper for analysis pipeline."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from copilot import (
    CopilotClient,
    CopilotSession,
    PermissionHandler,
    ProviderConfig,
)

from analysis.config import AnalysisSettings

logger = logging.getLogger(__name__)


async def create_analysis_session(
    model: str | None = None,
    system_message: str | None = None,
    tools: list | None = None,
) -> tuple[CopilotClient, CopilotSession]:
    """Create a Copilot SDK session configured for analysis work.

    Uses :class:`AnalysisSettings` loaded from environment variables for
    provider configuration defaults.  The caller is responsible for calling
    ``await client.stop()`` when done.

    Args:
        model: LLM model override (defaults to ``AnalysisSettings.model``).
        system_message: Optional system prompt appended to the default.
        tools: Optional list of custom tools to expose to the session.

    Returns:
        A ``(client, session)`` tuple.

    Raises:
        RuntimeError: If ``OPENAI_API_KEY`` is not set.
    """
    settings = AnalysisSettings.from_env()

    client = CopilotClient()
    await client.start()

    provider: ProviderConfig = {
        "type": "openai",
        "base_url": settings.base_url,
        "api_key": settings.api_key,
    }
    if settings.provider_type == "azure":
        provider["wire_api"] = "responses"

    kwargs: dict[str, Any] = {
        "on_permission_request": PermissionHandler.approve_all,
        "model": model or settings.model,
        "provider": provider,
    }

    if tools:
        kwargs["tools"] = tools
    if system_message:
        kwargs["system_message"] = {"content": system_message}

    session = await client.create_session(**kwargs)
    logger.info("Analysis session created (model=%s)", kwargs["model"])
    return client, session


async def send_message(
    session: CopilotSession,
    message: str,
    *,
    timeout: float = 120.0,
) -> str:
    """Send a user message and return the full assistant response text.

    Args:
        session: An active :class:`CopilotSession`.
        message: The user message to send.
        timeout: Maximum seconds to wait for a response.

    Returns:
        The assistant's response text.

    Raises:
        RuntimeError: If no response or empty content is received.
        TimeoutError: If the model does not respond within *timeout*.
    """
    logger.debug("Sending message (%d chars)", len(message))
    event = await session.send_and_wait(message, timeout=timeout)

    if event is None:
        raise RuntimeError("No response received from the model")

    content = event.data.content
    if content is None:
        raise RuntimeError("Response contained no text content")

    logger.debug("Received response (%d chars)", len(content))
    return content


@asynccontextmanager
async def analysis_session(
    system_message: str | None = None,
    model: str | None = None,
) -> AsyncGenerator[CopilotSession, None]:
    """Async context manager for a fully managed analysis session.

    Handles client start-up, session creation, and clean shutdown::

        async with analysis_session("You are an analyst.") as session:
            reply = await send_message(session, "Summarise this update …")

    Args:
        system_message: Optional system prompt.
        model: LLM model override.

    Yields:
        An active :class:`CopilotSession`.
    """
    client, session = await create_analysis_session(
        model=model,
        system_message=system_message,
    )
    try:
        async with session:
            yield session
    finally:
        await client.stop()
        logger.debug("Copilot client stopped")
