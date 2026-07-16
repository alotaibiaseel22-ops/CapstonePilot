from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from app.domain.enums import ProjectStatus


@dataclass
class Project:
    id: UUID
    name: str
    description: str
    status: ProjectStatus
    owner_id: UUID
    start_date: date | None
    due_date: date | None
    created_at: datetime
