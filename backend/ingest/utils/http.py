"""Shared HTTP client with automatic retry on transient errors."""

from __future__ import annotations

import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


def create_session(
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    status_forcelist: tuple = (429, 500, 502, 503, 504),
    timeout: int = 30,
) -> requests.Session:
    """Create a requests Session with automatic retry on transient errors.

    Uses urllib3 ``Retry`` with ``HTTPAdapter`` so retries are handled at the
    transport layer for both HTTP and HTTPS.

    Parameters
    ----------
    max_retries:
        Total number of retries per request.
    backoff_factor:
        Delay multiplier between retries (urllib3 formula).
    status_forcelist:
        HTTP status codes that trigger a retry.
    timeout:
        Default request timeout in seconds.  Stored on the session as
        ``session.default_timeout`` for callers that omit ``timeout=``.
    """
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=list(status_forcelist),
        allowed_methods=["GET", "HEAD", "OPTIONS"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (compatible; microsoft-news/1.0; "
                "+https://github.com/cheolhuikim/microsoft-news)"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    )

    # Attach default timeout so scrapers don't need to repeat it.
    session.default_timeout = timeout  # type: ignore[attr-defined]

    # Override request to inject default timeout when not provided.
    _original_request = session.request

    def _request_with_timeout(*args, **kwargs):
        kwargs.setdefault("timeout", timeout)
        return _original_request(*args, **kwargs)

    session.request = _request_with_timeout  # type: ignore[assignment]

    logger.debug(
        "Created HTTP session (retries=%d, backoff=%.1f, timeout=%ds)",
        max_retries,
        backoff_factor,
        timeout,
    )
    return session
