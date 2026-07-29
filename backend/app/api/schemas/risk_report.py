from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RiskReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    plan_version: int
    severity: str
    category: str
    title: str
    description: str
    created_at: datetime
