from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas.invitation import InvitationAcceptResult, InvitationEmailCreate, InvitationRead
from app.api.v1.deps import get_current_user, get_invitation_service, require_role
from app.application.services.invitation_service import (
    AlreadyAMemberError,
    InvitationAlreadyAcceptedError,
    InvitationEmailMismatchError,
    InvitationNotFoundError,
    InvitationRevokedError,
    InvitationService,
    NotProjectOwnerError,
    ProjectNotFoundError,
)
from app.domain.entities import User
from app.domain.enums import UserRole

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
):
    try:
        result = invitation_service.accept_invitation(token, current_user)
    except InvitationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvitationRevokedError as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc
    except InvitationAlreadyAcceptedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvitationEmailMismatchError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return InvitationAcceptResult(project_id=result.project_id)
