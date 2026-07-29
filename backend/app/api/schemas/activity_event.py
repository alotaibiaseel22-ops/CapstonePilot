from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ActivityEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    actor_id: UUID | None
    event_type: str
    message: str
    created_at: datetime


class UnreadCountRead(BaseModel):
    count: int
