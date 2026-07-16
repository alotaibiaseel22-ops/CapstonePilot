from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums import InvitationStatus


@dataclass
class Invitation:
    id: UUID
    project_id: UUID
    email: str | None
    token: str
    status: InvitationStatus
    invited_by: UUID
    created_at: datetime
    accepted_at: datetime | None
    accepted_by: UUID | None
    # None for link invitations, which only expire when the owner revokes them.
    # Set for email invitations, which expire 7 days after being (re)sent.
    expires_at: datetime | None
