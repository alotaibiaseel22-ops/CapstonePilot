from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from app.domain.enums import TaskPriority, TaskStatus


@dataclass
class Task:
    id: UUID
    milestone_id: UUID
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee_id: UUID | None
    # Mutually exclusive with assignee_id - a task is assigned to a real
    # User or to a Guest, never both (enforced in TaskService and by a DB
    # check constraint on the tasks table). None for unassigned tasks.
    assignee_guest_id: UUID | None
    due_date: date | None
    created_at: datetime
    updated_at: datetime
