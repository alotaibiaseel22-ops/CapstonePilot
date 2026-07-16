from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class ProjectMember:
    id: UUID
    project_id: UUID
    user_id: UUID
    added_at: datetime
