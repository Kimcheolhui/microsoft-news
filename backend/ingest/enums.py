"""Standard classification enums for update enrichment."""

from __future__ import annotations

UPDATE_TYPES: list[str] = [
    "new_feature",
    "retirement",
    "preview",
    "ga",
    "update",
    "security",
    "pricing",
    "deprecation",
    "guide",
    "case_study",
    "announcement",
    "event",
]

CATEGORIES: list[str] = [
    "compute",
    "database",
    "ai_ml",
    "networking",
    "storage",
    "security",
    "devtools",
    "analytics",
    "integration",
    "management",
    "iot",
    "mixed_reality",
    "other",
]

UPDATE_TYPE_LABELS: dict[str, str] = {
    "new_feature": "신규 기능",
    "retirement": "서비스 종료",
    "preview": "프리뷰/베타",
    "ga": "정식 출시 (GA)",
    "update": "기능 개선/변경",
    "security": "보안 패치/공지",
    "pricing": "가격 변경",
    "deprecation": "지원 중단 예고",
    "guide": "가이드/튜토리얼",
    "case_study": "사용 사례",
    "announcement": "공지",
    "event": "이벤트/행사",
}

CATEGORY_LABELS: dict[str, str] = {
    "compute": "컴퓨팅",
    "database": "데이터베이스",
    "ai_ml": "AI/ML",
    "networking": "네트워킹",
    "storage": "스토리지",
    "security": "보안",
    "devtools": "개발 도구",
    "analytics": "분석",
    "integration": "통합",
    "management": "관리",
    "iot": "IoT",
    "mixed_reality": "혼합 현실",
    "other": "기타",
}
