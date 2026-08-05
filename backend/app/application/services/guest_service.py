import uuid
from datetime import UTC, datetime

from app.application.ports.guest_repository import GuestRepository
from app.application.ports.invitation_repository import InvitationRepository
from app.domain.entities import Guest, Invitation
from app.domain.enums import InvitationStatus


class GuestNotFoundError(Exception):
    pass


class GuestAccessRevokedError(Exception):
    pass


class GuestService:
    def __init__(
        self, guest_repository: GuestRepository, invitation_repository: InvitationRepository
    ):
        self._guests = guest_repository
        self._invitations = invitation_repository

    def create_guest(self, invitation: Invitation, display_name: str) -> Guest:
        guest = Guest(
            id=uuid.uuid4(),
            project_id=invitation.project_id,
            invitation_id=invitation.id,
            display_name=display_name,
            created_at=datetime.now(UTC),
        )
        return self._guests.create(guest)

    def resolve_guest(self, guest_id: uuid.UUID, expected_project_id: uuid.UUID) -> Guest:
        """Mandatory DB lookup (mirrors get_current_user's mandatory User
        lookup) plus a live invitation-status check - single source of truth
        for "is this guest token still good," used by both the
        guest-session endpoint and require_project_access (deps.py). A
        revoked invitation cuts off every already-issued guest token for it
        immediately, not just future joins, since this re-checks the
        invitation's live status on every call rather than trusting the
        guest row alone."""
        guest = self._guests.get_by_id(guest_id)
        if guest is None or guest.project_id != expected_project_id:
            # A project_id mismatch is treated identically to "not found",
            # not "forbidden" - a guest token for project A must reveal
            # nothing about whether project B even exists.
            raise GuestNotFoundError(f"Guest {guest_id} not found")
        invitation = self._invitations.get_by_id(guest.invitation_id)
        if invitation is None or invitation.status == InvitationStatus.REVOKED:
            raise GuestAccessRevokedError("This guest session is no longer valid")
        return guest
