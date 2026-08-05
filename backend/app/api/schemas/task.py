from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.enums import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: UUID | None = None
    assignee_guest_id: UUID | None = None
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: UUID | None = None
    assignee_guest_id: UUID | None = None
    due_date: date | None = None


class TaskStatusUpdate(BaseModel):
    """Restricted update body for guests - status only, nothing else on the
    task is guest-mutable. See TaskService.update_status_as_guest."""

    status: TaskStatus


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    milestone_id: UUID
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee_id: UUID | None
    assignee_guest_id: UUID | None
    due_date: date | None
    created_at: datetime
