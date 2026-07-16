from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.schemas.project_member import ProjectMemberRead
from app.api.v1.deps import get_current_user, get_project_member_service, require_role
from app.application.services.project_member_service import ProjectMemberService
from app.domain.entities import User
from app.domain.enums import UserRole

router = APIRouter(tags=["project-members"])


@router.get("/projects/{project_id}/members", response_model=list[ProjectMemberRead])
def list_members(
    project_id: UUID,
    _current_user: User = Depends(get_current_user),
    member_service: ProjectMemberService = Depends(get_project_member_service),
):
    return [ProjectMemberRead.model_validate(m) for m in member_service.list_members(project_id)]


@router.delete("/projects/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    project_id: UUID,
    user_id: UUID,
    _owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    member_service: ProjectMemberService = Depends(get_project_member_service),
):
    member_service.remove_member(project_id, user_id)
