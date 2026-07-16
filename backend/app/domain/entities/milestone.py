from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass
class Milestone:
    id: UUID
    plan_id: UUID
    title: str
    due_date: date | None
    order: int
    created_at: datetime
