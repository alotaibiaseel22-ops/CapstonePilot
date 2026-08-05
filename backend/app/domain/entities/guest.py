from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Guest:
    """A guest is explicitly NOT a User - no email, no password, no login
    capability, no access beyond the single project it's bound to. Created
    when someone joins a shareable link invitation with just a display name
    (see GuestService.create_guest / invitations.py's guest-join route)."""

    id: UUID
    project_id: UUID
    invitation_id: UUID
    display_name: str
    created_at: datetime
