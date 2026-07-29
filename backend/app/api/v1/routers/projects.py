from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.api.v1.deps import (
    get_activity_service,
    get_current_user,
    get_project_service,
    get_risk_orchestrator,
    get_session_factory,
    get_user_repository,
    require_role,
)
from app.application.ports.risk_orchestrator import RiskAnalysisOrchestratorPort
from app.application.ports.user_repository import UserRepository
from app.application.services.activity_service import ActivityService
from app.application.services.project_service import (
    NotProjectOwnerError,
    ProjectNotFoundError,
    ProjectService,
)
from app.domain.entities import Project, User
from app.domain.enums import UserRole
from app.infrastructure.scheduler import run_immediate_risk_check

router = APIRouter(prefix="/projects", tags=["projects"])


def _to_project_read(project: Project, user_repository: UserRepository) -> ProjectRead:
    owner = user_repository.get_by_id(project.owner_id)
    read = ProjectRead.model_validate(project)
    if owner is not None:
        read.owner_name = owner.name
        read.owner_email = owner.email
    return read


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    background_tasks: BackgroundTasks,
    owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    project_service: ProjectService = Depends(get_project_service),
    user_repository: UserRepository = Depends(get_user_repository),
    session_factory=Depends(get_session_factory),
    risk_orchestrator: RiskAnalysisOrchestratorPort = Depends(get_risk_orchestrator),
    activity_service: ActivityService = Depends(get_activity_service),
):
    project = project_service.create_project(
        name=payload.name,
        description=payload.description,
        owner_id=owner.id,
        start_date=payload.start_date,
        due_date=payload.due_date,
    )
    activity_service.log_project_created(project, owner)
    # A brand-new project has no tasks yet, so this is a no-op in practice
    # today (compute_signals never breaches with zero tasks) - wired anyway
    # for consistency with every other project-affecting event, and in case
    # a project is ever created with an already-past due_date.
    background_tasks.add_task(
        run_immediate_risk_check, session_factory, risk_orchestrator, project_id=project.id
    )
    return _to_project_read(project, user_repository)


@router.get("", response_model=list[ProjectRead])
def list_projects(
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    user_repository: UserRepository = Depends(get_user_repository),
):
    return [
        _to_project_read(p, user_repository)
        for p in project_service.list_projects(current_user.id)
    ]


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: UUID,
    _current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    user_repository: UserRepository = Depends(get_user_repository),
):
    try:
        return _to_project_read(project_service.get_project(project_id), user_repository)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    background_tasks: BackgroundTasks,
    owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    project_service: ProjectService = Depends(get_project_service),
    user_repository: UserRepository = Depends(get_user_repository),
    session_factory=Depends(get_session_factory),
    risk_orchestrator: RiskAnalysisOrchestratorPort = Depends(get_risk_orchestrator),
):
    try:
        updates = payload.model_dump(exclude_unset=True)
        project = project_service.update_project(project_id, owner.id, **updates)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotProjectOwnerError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    # Covers "deadline changes" on the project's own due_date - check
    # immediately rather than waiting for the next scheduler tick.
    background_tasks.add_task(
        run_immediate_risk_check, session_factory, risk_orchestrator, project_id=project.id
    )
    return _to_project_read(project, user_repository)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    project_service: ProjectService = Depends(get_project_service),
):
    try:
        project_service.delete_project(project_id, owner.id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotProjectOwnerError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
