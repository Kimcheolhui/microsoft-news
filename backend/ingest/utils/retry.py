"""Reusable retry decorator with exponential backoff."""

from __future__ import annotations

import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """Decorator that retries a function with exponential backoff.

    Parameters
    ----------
    max_retries:
        Maximum number of retry attempts after the initial call.
    base_delay:
        Initial delay in seconds before the first retry.
    max_delay:
        Upper bound on the delay between retries.
    backoff_factor:
        Multiplier applied to the delay on each subsequent retry.
    exceptions:
        Tuple of exception types that trigger a retry.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc: Exception | None = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_retries:
                        delay = min(base_delay * backoff_factor ** attempt, max_delay)
                        logger.warning(
                            "Retry %d/%d for %s after error: %s (delay=%.1fs)",
                            attempt + 1,
                            max_retries,
                            func.__qualname__,
                            exc,
                            delay,
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            "All %d retries exhausted for %s: %s",
                            max_retries,
                            func.__qualname__,
                            exc,
                        )
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator
