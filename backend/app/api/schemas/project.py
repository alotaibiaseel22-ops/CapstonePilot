from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.enums import ProjectStatus


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    start_date: date | None = None
    due_date: date | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None
    start_date: date | None = None
    due_date: date | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    status: ProjectStatus
    owner_id: UUID
    owner_name: str | None = None
    owner_email: str | None = None
    start_date: date | None
    due_date: date | None
    created_at: datetime
