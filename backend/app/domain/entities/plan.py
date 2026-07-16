from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.enums import PlanStatus


@dataclass
class Plan:
    id: UUID
    project_id: UUID
    version: int
    status: PlanStatus
    rationale: dict[str, Any]
    created_at: datetime
