"""Tests for the update enrichment pipeline."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from analysis.prompts.enrichment import build_enrichment_prompt, ENRICHMENT_SYSTEM_PROMPT
from analysis.pipeline.enrichment import _validate_list, enrich_update
from ingest.enums import UPDATE_TYPES, CATEGORIES


class TestEnums:
    def test_update_types_are_strings(self):
        assert all(isinstance(t, str) for t in UPDATE_TYPES)
        assert len(UPDATE_TYPES) == 12
        assert "new_feature" in UPDATE_TYPES
        assert "deprecation" in UPDATE_TYPES

    def test_categories_are_strings(self):
        assert all(isinstance(c, str) for c in CATEGORIES)
        assert len(CATEGORIES) == 13
        assert "ai_ml" in CATEGORIES
        assert "other" in CATEGORIES


class TestValidateList:
    def test_valid_values(self):
        result = _validate_list(["new_feature", "preview"], UPDATE_TYPES)
        assert result == ["new_feature", "preview"]

    def test_filters_invalid(self):
        result = _validate_list(["new_feature", "bogus"], UPDATE_TYPES)
        assert result == ["new_feature"]

    def test_none_input(self):
        assert _validate_list(None, UPDATE_TYPES) == []

    def test_non_list_input(self):
        assert _validate_list("new_feature", UPDATE_TYPES) == []

    def test_empty_list(self):
        assert _validate_list([], UPDATE_TYPES) == []


class TestPrompt:
    def test_build_prompt_includes_title(self):
        prompt = build_enrichment_prompt("AKS Update", "New feature body text", "azure-updates-rss", "2026-03-24")
        assert "AKS Update" in prompt
        assert "New feature body text" in prompt
        assert "azure-updates-rss" in prompt

    def test_build_prompt_includes_enum_values(self):
        prompt = build_enrichment_prompt("Test", None, "test", None)
        assert "new_feature" in prompt
        assert "deprecation" in prompt
        assert "ai_ml" in prompt
        assert "compute" in prompt

    def test_build_prompt_handles_none(self):
        prompt = build_enrichment_prompt("Test", None, "test", None)
        assert "(no content)" in prompt
        assert "unknown" in prompt

    def test_system_prompt_exists(self):
        assert "JSON" in ENRICHMENT_SYSTEM_PROMPT
        assert "classify" in ENRICHMENT_SYSTEM_PROMPT.lower()


class TestEnrichUpdate:
    @pytest.fixture
    def mock_update(self):
        class FakeUpdate:
            id = "test-id"
            title = "Azure Kubernetes Service now supports GPU"
            body = "AKS adds GPU node pools for ML workloads. This enables data scientists to run training jobs directly on AKS."
            published_date = "2026-03-24"
        return FakeUpdate()

    async def test_successful_enrichment(self, mock_update):
        llm_response = json.dumps({
            "update_types": ["new_feature"],
            "categories": ["compute", "ai_ml"],
            "services_affected": ["Azure Kubernetes Service"],
            "summary": "AKS now supports GPU node pools for ML workloads.",
            "title_ko": "Azure Kubernetes Service에 GPU 지원 추가",
            "summary_ko": "AKS에서 ML 워크로드를 위한 GPU 노드 풀 추가"
        })

        mock_session = AsyncMock()
        with patch("analysis.pipeline.enrichment.send_message", return_value=llm_response):
            result = await enrich_update(mock_session, mock_update, "azure-updates-rss")

        assert result is not None
        assert result["update_types"] == ["new_feature"]
        assert "compute" in result["categories"]
        assert "ai_ml" in result["categories"]
        assert "Azure Kubernetes Service" in result["services_affected"]
        assert "GPU" in result["title_ko"]

    async def test_filters_invalid_types(self, mock_update):
        llm_response = json.dumps({
            "update_types": ["new_feature", "invalid_type"],
            "categories": ["compute", "invalid_cat"],
            "services_affected": ["AKS"],
            "summary": "Test summary",
            "title_ko": "테스트",
            "summary_ko": "테스트 요약"
        })

        mock_session = AsyncMock()
        with patch("analysis.pipeline.enrichment.send_message", return_value=llm_response):
            result = await enrich_update(mock_session, mock_update, "test")

        assert result["update_types"] == ["new_feature"]
        assert result["categories"] == ["compute"]

    async def test_llm_failure_returns_none(self, mock_update):
        mock_session = AsyncMock()
        with patch("analysis.pipeline.enrichment.send_message", side_effect=RuntimeError("LLM error")):
            result = await enrich_update(mock_session, mock_update, "test")

        assert result is None

    async def test_multi_select_types(self, mock_update):
        llm_response = json.dumps({
            "update_types": ["new_feature", "preview"],
            "categories": ["ai_ml", "security"],
            "services_affected": ["Azure OpenAI", "Azure Key Vault"],
            "summary": "Test",
            "title_ko": "테스트",
            "summary_ko": "테스트"
        })

        mock_session = AsyncMock()
        with patch("analysis.pipeline.enrichment.send_message", return_value=llm_response):
            result = await enrich_update(mock_session, mock_update, "test")

        assert result["update_types"] == ["new_feature", "preview"]
        assert result["categories"] == ["ai_ml", "security"]
