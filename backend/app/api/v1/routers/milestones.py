from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api.schemas.milestone import MilestoneCreate, MilestoneRead, MilestoneUpdate
from app.api.v1.deps import (
    get_current_user,
    get_milestone_service,
    get_risk_orchestrator,
    get_session_factory,
    require_role,
)
from app.application.ports.risk_orchestrator import RiskAnalysisOrchestratorPort
from app.application.services.milestone_service import MilestoneNotFoundError, MilestoneService
from app.domain.entities import User
from app.domain.enums import UserRole
from app.infrastructure.scheduler import run_immediate_risk_check

router = APIRouter(tags=["milestones"])


@router.post(
    "/projects/{project_id}/milestones",
    response_model=MilestoneRead,
    status_code=status.HTTP_201_CREATED,
)
def create_milestone(
    project_id: UUID,
    payload: MilestoneCreate,
    _owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    milestone_service: MilestoneService = Depends(get_milestone_service),
):
    try:
        milestone = milestone_service.create_milestone(
            project_id=project_id,
            title=payload.title,
            due_date=payload.due_date,
            order=payload.order,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MilestoneRead.model_validate(milestone)


@router.get("/projects/{project_id}/milestones", response_model=list[MilestoneRead])
def list_milestones(
    project_id: UUID,
    _current_user: User = Depends(get_current_user),
    milestone_service: MilestoneService = Depends(get_milestone_service),
):
    return [MilestoneRead.model_validate(m) for m in milestone_service.list_milestones(project_id)]


@router.get("/milestones/{milestone_id}", response_model=MilestoneRead)
def get_milestone(
    milestone_id: UUID,
    _current_user: User = Depends(get_current_user),
    milestone_service: MilestoneService = Depends(get_milestone_service),
):
    try:
        return MilestoneRead.model_validate(milestone_service.get_milestone(milestone_id))
    except MilestoneNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/milestones/{milestone_id}", response_model=MilestoneRead)
def update_milestone(
    milestone_id: UUID,
    payload: MilestoneUpdate,
    background_tasks: BackgroundTasks,
    _owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    milestone_service: MilestoneService = Depends(get_milestone_service),
    session_factory=Depends(get_session_factory),
    risk_orchestrator: RiskAnalysisOrchestratorPort = Depends(get_risk_orchestrator),
):
    try:
        updates = payload.model_dump(exclude_unset=True)
        milestone = milestone_service.update_milestone(milestone_id, **updates)
    except MilestoneNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    # A milestone due-date change (there's no separate "milestone completion"
    # concept in the domain model - completion is implicit in its tasks) can
    # shift the project's schedule variance - check immediately.
    background_tasks.add_task(
        run_immediate_risk_check, session_factory, risk_orchestrator, milestone_id=milestone.id
    )

    return MilestoneRead.model_validate(milestone)


@router.delete("/milestones/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_milestone(
    milestone_id: UUID,
    _owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    milestone_service: MilestoneService = Depends(get_milestone_service),
):
    milestone_service.delete_milestone(milestone_id)
