from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.api.v1.deps import get_current_user, get_project_service, require_role
from app.application.services.project_service import ProjectNotFoundError, ProjectService
from app.domain.entities import User
from app.domain.enums import UserRole

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    project_service: ProjectService = Depends(get_project_service),
):
    project = project_service.create_project(
        name=payload.name,
        description=payload.description,
        owner_id=owner.id,
        start_date=payload.start_date,
        due_date=payload.due_date,
    )
    return ProjectRead.model_validate(project)


@router.get("", response_model=list[ProjectRead])
def list_projects(
    _current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
):
    return [ProjectRead.model_validate(p) for p in project_service.list_projects()]


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: UUID,
    _current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
):
    try:
        return ProjectRead.model_validate(project_service.get_project(project_id))
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    _owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    project_service: ProjectService = Depends(get_project_service),
):
    try:
        updates = payload.model_dump(exclude_unset=True)
        project = project_service.update_project(project_id, **updates)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProjectRead.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    _owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    project_service: ProjectService = Depends(get_project_service),
):
    project_service.delete_project(project_id)
