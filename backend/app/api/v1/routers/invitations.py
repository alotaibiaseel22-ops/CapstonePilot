from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.api.schemas.auth import UserRead
from app.api.schemas.guest import GuestJoinRequest, GuestRead, GuestSessionRead
from app.api.schemas.invitation import (
    InvitationAcceptResult,
    InvitationEmailCreate,
    InvitationOnboardRequest,
    InvitationOnboardResponse,
    InvitationPreviewRead,
    InvitationRead,
)
from app.api.v1.deps import (
    get_activity_service,
    get_auth_service,
    get_current_user,
    get_guest_service,
    get_invitation_service,
    guest_bearer_scheme,
    require_role,
)
from app.application.services.activity_service import ActivityService
from app.application.services.auth_service import AuthService, EmailAlreadyRegisteredError
from app.application.services.guest_service import (
    GuestAccessRevokedError,
    GuestNotFoundError,
    GuestService,
)
from app.application.services.invitation_service import (
    AlreadyAMemberError,
    InvitationAlreadyAcceptedError,
    InvitationEmailMismatchError,
    InvitationExpiredError,
    InvitationNotEmailBasedError,
    InvitationNotFoundError,
    InvitationNotLinkBasedError,
    InvitationNotResendableError,
    InvitationRevokedError,
    InvitationService,
    NotProjectOwnerError,
    ProjectNotFoundError,
)
from app.domain.entities import User
from app.domain.enums import UserRole
from app.infrastructure.security.jwt import (
    create_access_token,
    create_guest_access_token,
    decode_guest_access_token,
)

router = APIRouter(tags=["invitations"])


@router.post(
    "/projects/{project_id}/invitations",
    response_model=list[InvitationRead],
    status_code=status.HTTP_201_CREATED,
)
def invite_by_email(
    project_id: UUID,
    payload: InvitationEmailCreate,
    owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    try:
        invitations = invitation_service.invite_by_emails(project_id, payload.emails, owner.id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotProjectOwnerError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except AlreadyAMemberError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return [InvitationRead.model_validate(i) for i in invitations]


@router.post("/projects/{project_id}/invitations/link", response_model=InvitationRead)
def get_or_create_link_invitation(
    project_id: UUID,
    owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    try:
        invitation = invitation_service.get_or_create_link_invitation(project_id, owner.id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotProjectOwnerError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return InvitationRead.model_validate(invitation)


@router.post("/projects/{project_id}/invitations/link/regenerate", response_model=InvitationRead)
def regenerate_link_invitation(
    project_id: UUID,
    owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    try:
        invitation = invitation_service.regenerate_link_invitation(project_id, owner.id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotProjectOwnerError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return InvitationRead.model_validate(invitation)


@router.get("/projects/{project_id}/invitations", response_model=list[InvitationRead])
def list_project_invitations(
    project_id: UUID,
    owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    try:
        invitations = invitation_service.list_invitations(project_id, owner.id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotProjectOwnerError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return [InvitationRead.model_validate(i) for i in invitations]


@router.get("/invitations/mine", response_model=list[InvitationRead])
def list_my_invitations(
    current_user: User = Depends(get_current_user),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    invitations = invitation_service.list_pending_for_user(current_user.email)
    return [InvitationRead.model_validate(i) for i in invitations]


@router.get("/invitations/{token}/preview", response_model=InvitationPreviewRead)
def preview_invitation(
    token: str,
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    """Public, unauthenticated: lets the invite-accept page decide whether to
    send a first-time visitor to Sign Up or Log In before they've proven who
    they are. Only exposes what someone holding the token already implies."""
    try:
        preview = invitation_service.preview(token)
    except InvitationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return InvitationPreviewRead.model_validate(preview)


@router.post("/invitations/{token}/onboard", response_model=InvitationOnboardResponse)
def onboard_via_invitation(
    token: str,
    payload: InvitationOnboardRequest,
    auth_service: AuthService = Depends(get_auth_service),
    invitation_service: InvitationService = Depends(get_invitation_service),
    activity_service: ActivityService = Depends(get_activity_service),
):
    """Public, unauthenticated: the name-only "join the project" flow for
    email invitations. The invited email always comes from the token on the
    server (get_email_invitation_or_raise), never from the request body -
    the frontend never sends an email here at all. Falls back to a 409 if
    the email already has an account, so an invitation link can never be
    used as a password-less login for an existing account."""
    try:
        invitation = invitation_service.get_email_invitation_or_raise(token)
    except InvitationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvitationNotEmailBasedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except (InvitationRevokedError, InvitationExpiredError) as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc
    except InvitationAlreadyAcceptedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    try:
        user = auth_service.provision_invited_user(payload.name, invitation.email)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    result = invitation_service.accept_invitation(token, user)
    activity_service.log_member_joined(result.project_id, user)
    token_str = create_access_token(user.id)
    return InvitationOnboardResponse(
        access_token=token_str,
        user=UserRead.model_validate(user),
        project_id=result.project_id,
    )


@router.post("/invitations/{token}/guest-join", response_model=GuestSessionRead)
def guest_join(
    token: str,
    payload: GuestJoinRequest,
    invitation_service: InvitationService = Depends(get_invitation_service),
    guest_service: GuestService = Depends(get_guest_service),
):
    """Public, unauthenticated: the Figma/Canva-style "join with just a
    name" flow for shareable link invitations. Always creates a new Guest
    row + a fresh signed guest token - the frontend should call
    GET /invitations/{token}/guest-session first with any stored token to
    avoid double-joining on a return visit (see that route below)."""
    try:
        invitation = invitation_service.start_guest_session(token)
    except InvitationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvitationNotLinkBasedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except (InvitationRevokedError, InvitationExpiredError) as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc

    guest = guest_service.create_guest(invitation, payload.display_name)
    return GuestSessionRead(
        guest_access_token=create_guest_access_token(guest.id, guest.project_id),
        project_id=guest.project_id,
        guest=GuestRead.model_validate(guest),
    )


@router.get("/invitations/{token}/guest-session", response_model=GuestSessionRead)
def get_guest_session(
    token: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(guest_bearer_scheme),
    invitation_service: InvitationService = Depends(get_invitation_service),
    guest_service: GuestService = Depends(get_guest_service),
):
    """Public: resumes an already-issued guest session (a stored token from
    a previous visit) without creating a new Guest row, so a returning
    visitor skips the name prompt. Never mutates anything - a missing or
    no-longer-valid token is just a 401, telling the frontend to fall back
    to guest-join."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No guest session token provided"
        )
    payload = decode_guest_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired guest session"
        )

    try:
        invitation = invitation_service.start_guest_session(token)
    except (InvitationNotFoundError, InvitationNotLinkBasedError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (InvitationRevokedError, InvitationExpiredError) as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc

    try:
        guest = guest_service.resolve_guest(payload.guest_id, invitation.project_id)
    except (GuestNotFoundError, GuestAccessRevokedError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return GuestSessionRead(
        guest_access_token=credentials.credentials,
        project_id=guest.project_id,
        guest=GuestRead.model_validate(guest),
    )


@router.post("/invitations/{invitation_id}/resend", response_model=InvitationRead)
def resend_invitation(
    invitation_id: UUID,
    owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    try:
        invitation = invitation_service.resend_invitation(invitation_id, owner.id)
    except InvitationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotProjectOwnerError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InvitationNotResendableError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return InvitationRead.model_validate(invitation)


@router.delete("/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invitation(
    invitation_id: UUID,
    owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    try:
        invitation_service.revoke_invitation(invitation_id, owner.id)
    except InvitationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotProjectOwnerError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/invitations/{token}/accept", response_model=InvitationAcceptResult)
def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    invitation_service: InvitationService = Depends(get_invitation_service),
    activity_service: ActivityService = Depends(get_activity_service),
):
    try:
        result = invitation_service.accept_invitation(token, current_user)
    except InvitationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (InvitationRevokedError, InvitationExpiredError) as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc
    except InvitationAlreadyAcceptedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvitationEmailMismatchError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    activity_service.log_member_joined(result.project_id, current_user)
    return InvitationAcceptResult(project_id=result.project_id)
