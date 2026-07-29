from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class ActivityEvent:
    id: UUID
    project_id: UUID
    actor_id: UUID | None
    event_type: str
    message: str
    created_at: datetime
