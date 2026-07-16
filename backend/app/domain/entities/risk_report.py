from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums import RiskSeverity


@dataclass
class RiskReport:
    id: UUID
    project_id: UUID
    plan_version: int
    severity: RiskSeverity
    category: str
    title: str
    description: str
    created_at: datetime
