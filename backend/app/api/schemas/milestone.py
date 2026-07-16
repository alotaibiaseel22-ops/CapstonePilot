from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MilestoneCreate(BaseModel):
    title: str
    due_date: date | None = None
    order: int = 0


class MilestoneUpdate(BaseModel):
    title: str | None = None
    due_date: date | None = None
    order: int | None = None


class MilestoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_id: UUID
    title: str
    due_date: date | None
    order: int
    created_at: datetime
