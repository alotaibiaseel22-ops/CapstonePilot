from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.enums import RecommendationStatus


@dataclass
class Recommendation:
    id: UUID
    risk_report_id: UUID | None
    project_id: UUID
    title: str
    category: str
    severity: str
    effort: str
    impact: str
    description: str
    rationale: str | None
    proposed_changes: dict[str, Any]
    status: RecommendationStatus
    created_at: datetime
