from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GuestJoinRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)


class GuestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    display_name: str
    created_at: datetime


class GuestSessionRead(BaseModel):
    guest_access_token: str
    token_type: str = "bearer"
    project_id: UUID
    guest: GuestRead
