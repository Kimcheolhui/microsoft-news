from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str
    log_level: str = "INFO"
    http_max_retries: int = 3
    http_backoff_factor: float = 0.5
    http_timeout: int = 30
    engine_max_retries: int = 2
    consecutive_failure_threshold: int = 3

    @classmethod
    def from_env(cls) -> Settings:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL environment variable is required")
        return cls(
            database_url=database_url,
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
            http_max_retries=int(os.environ.get("HTTP_MAX_RETRIES", "3")),
            http_backoff_factor=float(os.environ.get("HTTP_BACKOFF_FACTOR", "0.5")),
            http_timeout=int(os.environ.get("HTTP_TIMEOUT", "30")),
            engine_max_retries=int(os.environ.get("ENGINE_MAX_RETRIES", "2")),
            consecutive_failure_threshold=int(
                os.environ.get("CONSECUTIVE_FAILURE_THRESHOLD", "3")
            ),
        )


settings: Settings | None = None


def get_settings() -> Settings:
    global settings
    if settings is None:
        settings = Settings.from_env()
    return settings
