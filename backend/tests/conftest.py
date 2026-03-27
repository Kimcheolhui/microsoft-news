"""Shared test fixtures for microsoft-news test suite."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def sample_update():
    """Create a mock Update object with typical fields."""
    update = MagicMock()
    update.id = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    update.title = "Azure Kubernetes Service (AKS) now supports Node Autoprovision"
    update.summary = "AKS now supports automatic node provisioning."
    update.body = "Detailed body about AKS autoprovision feature."
    update.source_url = "https://azure.microsoft.com/updates/aks-autoprovision"
    update.published_date = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
    update.categories = ["Kubernetes", "Compute"]
    update.services_affected = ["AKS"]
    update.update_type = "new_feature"
    update.raw_data = {}
    return update


@pytest.fixture
def sample_scraped_content():
    """Scraped content dict as returned by deep_scraper."""
    return {
        "url": "https://azure.microsoft.com/updates/aks-autoprovision",
        "raw_length": 5000,
        "text": "Azure Kubernetes Service now supports Node Autoprovision...",
        "truncated": False,
    }


@pytest.fixture
def sample_scraped_content_error():
    """Scraped content dict when scraping fails."""
    return {
        "url": "https://example.com/broken",
        "error": "HTTP 404",
        "text": "",
    }


@pytest.fixture
def sample_research_data():
    """Research context dict as returned by researcher."""
    return {
        "keywords": ["Azure", "Kubernetes", "AKS", "Autoprovision"],
        "related_updates": [
            {
                "id": str(uuid.uuid4()),
                "title": "AKS cluster autoscaler improvements",
                "source_url": "https://azure.microsoft.com/updates/aks-autoscaler",
                "published_date": "2026-03-15T00:00:00+00:00",
                "summary": "Improvements to AKS autoscaler performance.",
            },
        ],
        "count": 1,
    }


@pytest.fixture
def sample_analysis_data():
    """Structured analysis dict as returned by the analyzer."""
    return {
        "update_type": "new_feature",
        "affected_services": ["Azure Kubernetes Service"],
        "impact_summary": "New autoprovision capability for AKS nodes.",
        "key_details": [
            "Automatic node pool creation based on workload demands",
            "Supports GPU and spot instance node pools",
        ],
        "action_items": [
            "Review existing node pool configurations",
            "Test autoprovision in staging environment",
        ],
    }


@pytest.fixture
def sample_report_content():
    """Bilingual report dict as returned by the writer."""
    return {
        "title_ko": "AKS 노드 자동 프로비저닝 지원",
        "title_en": "AKS Now Supports Node Autoprovision",
        "summary_ko": "Azure Kubernetes Service에서 노드 자동 프로비저닝 기능을 지원합니다.",
        "summary_en": "Azure Kubernetes Service now supports automatic node provisioning.",
        "body_ko": "## 개요\nAKS 노드 자동 프로비저닝...",
        "body_en": "## Overview\nAKS Node Autoprovision...",
    }
