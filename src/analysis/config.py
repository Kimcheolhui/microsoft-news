from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AnalysisSettings:
    provider_type: str  # "openai" or "azure"
    api_key: str
    base_url: str
    model: str = "gpt-5.4-mini"
    max_tokens_per_report: int = 8000
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> AnalysisSettings:
        provider = os.environ.get("LLM_PROVIDER", "openai").lower()

        if provider == "azure":
            api_key = os.environ.get("AZURE_OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "AZURE_OPENAI_API_KEY environment variable is required"
                )
            base_url = os.environ.get("AZURE_OPENAI_BASE_URL")
            if not base_url:
                raise RuntimeError(
                    "AZURE_OPENAI_BASE_URL environment variable is required"
                )
        else:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY environment variable is required"
                )
            base_url = os.environ.get(
                "OPENAI_BASE_URL", "https://api.openai.com/v1"
            )

        return cls(
            provider_type=provider,
            api_key=api_key,
            base_url=base_url,
            model=os.environ.get("ANALYSIS_MODEL", "gpt-5.4-mini"),
            max_tokens_per_report=int(
                os.environ.get("MAX_TOKENS_PER_REPORT", "8000")
            ),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )
