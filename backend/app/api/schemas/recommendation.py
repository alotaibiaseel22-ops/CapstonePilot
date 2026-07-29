from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RecommendationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    status: str
    created_at: datetime
