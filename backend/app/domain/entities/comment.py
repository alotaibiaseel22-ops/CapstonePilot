from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Comment:
    """A project-wide discussion entry. Exactly one of author_id/
    author_guest_id is set, never both, never neither - same "always has an
    author" rule as Attachment's uploader pair (see that entity's docstring
    for why this differs from Task's assignee pair, which allows neither)."""

    id: UUID
    project_id: UUID
    body: str
    author_id: UUID | None
    author_guest_id: UUID | None
    created_at: datetime
