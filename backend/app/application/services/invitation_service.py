import logging
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.application.ports.email_service import EmailService
from app.application.ports.invitation_repository import InvitationRepository
from app.application.ports.project_member_repository import ProjectMemberRepository
from app.application.ports.project_repository import ProjectRepository
from app.application.ports.user_repository import UserRepository
from app.core.config import settings
from app.domain.entities import Invitation, ProjectMember, User
from app.domain.enums import InvitationStatus

logger = logging.getLogger(__name__)

EMAIL_INVITATION_LIFETIME = timedelta(days=7)


class ProjectNotFoundError(Exception):
    pass


class NotProjectOwnerError(Exception):
    pass


class InvitationNotFoundError(Exception):
    pass


class InvitationRevokedError(Exception):
    pass


class InvitationExpiredError(Exception):
    pass


class InvitationAlreadyAcceptedError(Exception):
    pass


class InvitationEmailMismatchError(Exception):
    pass


class InvitationNotResendableError(Exception):
    pass


class AlreadyAMemberError(Exception):
    pass


class InvitationNotEmailBasedError(Exception):
    pass


class InvitationNotLinkBasedError(Exception):
    pass


@dataclass
class AcceptedInvitationResult:
    project_id: uuid.UUID


@dataclass
class InvitationPreview:
    project_name: str
    inviter_name: str
    email: str | None
    user_exists: bool
    is_valid: bool


class InvitationService:
    def __init__(
        self,
        invitation_repository: InvitationRepository,
        project_member_repository: ProjectMemberRepository,
        user_repository: UserRepository,
        project_repository: ProjectRepository,
        email_service: EmailService,
    ):
        self._invitations = invitation_repository
        self._members = project_member_repository
        self._users = user_repository
        self._projects = project_repository
        self._email_service = email_service

    def _assert_owner(self, project_id: uuid.UUID, user_id: uuid.UUID):
        project = self._projects.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project {project_id} not found")
        if project.owner_id != user_id:
            raise NotProjectOwnerError("Only this project's owner can manage its invitations")
        return project

    def _is_expired(self, invitation: Invitation) -> bool:
        return invitation.expires_at is not None and datetime.now(UTC) > invitation.expires_at

    def _send_invitation_email(self, invitation: Invitation, invited_by: uuid.UUID) -> None:
        project = self._projects.get_by_id(invitation.project_id)
        inviter = self._users.get_by_id(invited_by)
        if project is None or inviter is None or invitation.email is None:
            # This used to be a silent no-op - logged now purely for
            # visibility (still returns, still never raises), since a
            # missed lookup here is otherwise indistinguishable from an
            # actual send failure when debugging "invitation email never
            # arrived" from logs alone.
            logger.warning(
                "send_invitation_email() NOT called for invitation %s - "
                "project_found=%s inviter_found=%s email_present=%s",
                invitation.id,
                project is not None,
                inviter is not None,
                invitation.email is not None,
            )
            return
        logger.info(
            "Calling send_invitation_email() for invitation %s | to=%s | via=%s",
            invitation.id,
            invitation.email,
            type(self._email_service).__name__,
        )
        self._email_service.send_invitation_email(
            to_email=invitation.email,
            project_name=project.name,
            inviter_name=inviter.name,
            invite_url=f"{settings.FRONTEND_URL}/invite/{invitation.token}",
        )

    def invite_by_email(
        self, project_id: uuid.UUID, email: str, invited_by: uuid.UUID
    ) -> Invitation:
        self._assert_owner(project_id, invited_by)

        existing_user = self._users.get_by_email(email)
        if existing_user is not None and self._members.exists(project_id, existing_user.id):
            raise AlreadyAMemberError(f"{email} is already a member of this project")

        for existing in self._invitations.list_by_project(project_id):
            if existing.email == email and existing.status == InvitationStatus.PENDING:
                self._send_invitation_email(existing, invited_by)
                return existing

        now = datetime.now(UTC)
        invitation = Invitation(
            id=uuid.uuid4(),
            project_id=project_id,
            email=email,
            token=secrets.token_urlsafe(32),
            status=InvitationStatus.PENDING,
            invited_by=invited_by,
            created_at=now,
            accepted_at=None,
            accepted_by=None,
            expires_at=now + EMAIL_INVITATION_LIFETIME,
        )
        created = self._invitations.create(invitation)
        self._send_invitation_email(created, invited_by)
        return created

    def invite_by_emails(
        self, project_id: uuid.UUID, emails: list[str], invited_by: uuid.UUID
    ) -> list[Invitation]:
        return [self.invite_by_email(project_id, email, invited_by) for email in emails]

    def resend_invitation(
        self, invitation_id: uuid.UUID, requesting_user_id: uuid.UUID
    ) -> Invitation:
        invitation = self._invitations.get_by_id(invitation_id)
        if invitation is None:
            raise InvitationNotFoundError(f"Invitation {invitation_id} not found")
        self._assert_owner(invitation.project_id, requesting_user_id)

        if invitation.email is None:
            raise InvitationNotResendableError("Shareable links don't need to be resent")
        if invitation.status != InvitationStatus.PENDING:
            raise InvitationNotResendableError("Only pending invitations can be resent")

        invitation.expires_at = datetime.now(UTC) + EMAIL_INVITATION_LIFETIME
        updated = self._invitations.update(invitation)
        self._send_invitation_email(updated, requesting_user_id)
        return updated

    def _create_link_invitation(self, project_id: uuid.UUID, invited_by: uuid.UUID) -> Invitation:
        now = datetime.now(UTC)
        invitation = Invitation(
            id=uuid.uuid4(),
            project_id=project_id,
            email=None,
            token=secrets.token_urlsafe(32),
            status=InvitationStatus.PENDING,
            invited_by=invited_by,
            created_at=now,
            accepted_at=None,
            accepted_by=None,
            expires_at=now + timedelta(days=settings.INVITATION_LINK_EXPIRE_DAYS),
        )
        return self._invitations.create(invitation)

    def get_or_create_link_invitation(
        self, project_id: uuid.UUID, invited_by: uuid.UUID
    ) -> Invitation:
        self._assert_owner(project_id, invited_by)

        existing = self._invitations.get_active_link_invitation(project_id)
        if existing is not None:
            if not self._is_expired(existing):
                return existing
            # get_active_link_invitation only filters on status, not expiry -
            # without this check, an owner would silently be handed back an
            # already-dead link forever. Revoke it and fall through to
            # minting a fresh one, same as regenerate_link_invitation does.
            existing.status = InvitationStatus.REVOKED
            self._invitations.update(existing)

        return self._create_link_invitation(project_id, invited_by)

    def regenerate_link_invitation(
        self, project_id: uuid.UUID, invited_by: uuid.UUID
    ) -> Invitation:
        """Revokes whatever shareable link is currently active (if any) and
        mints a fresh one - old copies of the link stop working immediately."""
        self._assert_owner(project_id, invited_by)

        existing = self._invitations.get_active_link_invitation(project_id)
        if existing is not None:
            existing.status = InvitationStatus.REVOKED
            self._invitations.update(existing)

        return self._create_link_invitation(project_id, invited_by)

    def list_invitations(
        self, project_id: uuid.UUID, requesting_user_id: uuid.UUID
    ) -> list[Invitation]:
        self._assert_owner(project_id, requesting_user_id)
        return self._invitations.list_by_project(project_id)

    def list_pending_for_user(self, email: str) -> list[Invitation]:
        return [
            invitation
            for invitation in self._invitations.list_pending_by_email(email)
            if not self._is_expired(invitation)
        ]

    def revoke_invitation(self, invitation_id: uuid.UUID, requesting_user_id: uuid.UUID) -> None:
        invitation = self._invitations.get_by_id(invitation_id)
        if invitation is None:
            raise InvitationNotFoundError(f"Invitation {invitation_id} not found")
        self._assert_owner(invitation.project_id, requesting_user_id)
        invitation.status = InvitationStatus.REVOKED
        self._invitations.update(invitation)

    def preview(self, token: str) -> InvitationPreview:
        invitation = self._invitations.get_by_token(token)
        if invitation is None:
            raise InvitationNotFoundError("This invitation link is invalid")

        project = self._projects.get_by_id(invitation.project_id)
        project_name = project.name if project is not None else "this project"
        inviter = self._users.get_by_id(invitation.invited_by)
        inviter_name = inviter.name if inviter is not None else "Someone"

        user_exists = False
        if invitation.email is not None:
            user_exists = self._users.get_by_email(invitation.email) is not None

        is_valid = invitation.status == InvitationStatus.PENDING and not self._is_expired(
            invitation
        )
        return InvitationPreview(
            project_name=project_name,
            inviter_name=inviter_name,
            email=invitation.email,
            user_exists=user_exists,
            is_valid=is_valid,
        )

    def get_email_invitation_or_raise(self, token: str) -> Invitation:
        """Pre-check for the name-only onboarding flow (invitations.py's
        /onboard endpoint) - validates the token is a usable *email*
        invitation before any User is created for it. Does not create
        membership or change status; accept_invitation still does that once
        a User exists to pass it."""
        invitation = self._invitations.get_by_token(token)
        if invitation is None:
            raise InvitationNotFoundError("This invitation link is invalid")
        if invitation.email is None:
            raise InvitationNotEmailBasedError(
                "Shareable links don't carry an invited email - sign in or create an account"
            )
        if invitation.status == InvitationStatus.REVOKED:
            raise InvitationRevokedError("This invitation has been revoked")
        if invitation.status == InvitationStatus.ACCEPTED:
            raise InvitationAlreadyAcceptedError("This invitation has already been accepted")
        if self._is_expired(invitation):
            raise InvitationExpiredError("This invitation has expired")
        return invitation

    def start_guest_session(self, token: str) -> Invitation:
        """Pre-check for the guest-join/guest-session flow (invitations.py's
        /guest-join and /guest-session endpoints) - validates the token is a
        usable *link* invitation before any Guest is created for it. Mirrors
        get_email_invitation_or_raise, inverted: a targeted email invitation
        must go through /onboard (or full login/register), never guest-join -
        this keeps a guest link from being used to dodge the "invited email
        must match" check email invitations enforce."""
        invitation = self._invitations.get_by_token(token)
        if invitation is None:
            raise InvitationNotFoundError("This invitation link is invalid")
        if invitation.email is not None:
            raise InvitationNotLinkBasedError(
                "This is a personal invitation - sign in or create an account"
            )
        if invitation.status == InvitationStatus.REVOKED:
            raise InvitationRevokedError("This invitation has been revoked")
        if self._is_expired(invitation):
            raise InvitationExpiredError("This invitation has expired")
        return invitation

    def accept_invitation(self, token: str, user: User) -> AcceptedInvitationResult:
        invitation = self._invitations.get_by_token(token)
        if invitation is None:
            raise InvitationNotFoundError("This invitation link is invalid")

        if invitation.status == InvitationStatus.REVOKED:
            raise InvitationRevokedError("This invitation has been revoked")

        is_link_invitation = invitation.email is None

        if not is_link_invitation:
            if invitation.status == InvitationStatus.ACCEPTED:
                raise InvitationAlreadyAcceptedError("This invitation has already been accepted")
            if self._is_expired(invitation):
                raise InvitationExpiredError("This invitation has expired")
            if invitation.email != user.email:
                raise InvitationEmailMismatchError(
                    "This invitation was sent to a different email address"
                )

        if not self._members.exists(invitation.project_id, user.id):
            member = ProjectMember(
                id=uuid.uuid4(),
                project_id=invitation.project_id,
                user_id=user.id,
                added_at=datetime.now(UTC),
            )
            self._members.add(member)

        if not is_link_invitation:
            invitation.status = InvitationStatus.ACCEPTED
            invitation.accepted_at = datetime.now(UTC)
            invitation.accepted_by = user.id
            self._invitations.update(invitation)

        return AcceptedInvitationResult(project_id=invitation.project_id)
