from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.task import TaskCreate, TaskRead, TaskStatusUpdate, TaskUpdate
from app.api.v1.deps import (
    Actor,
    get_activity_service,
    get_current_user,
    get_db,
    get_risk_orchestrator,
    get_session_factory,
    get_task_service,
    require_project_access_for_milestone,
    require_project_access_for_task,
    require_role,
)
from app.application.ports.risk_orchestrator import RiskAnalysisOrchestratorPort
from app.application.services.activity_service import ActivityService
from app.application.services.task_service import (
    NotTaskAssigneeError,
    TaskNotFoundError,
    TaskService,
)
from app.domain.entities import User
from app.domain.enums import TaskStatus, UserRole
from app.infrastructure.scheduler import _resolve_project_id, run_immediate_risk_check

router = APIRouter(tags=["tasks"])


@router.post(
    "/milestones/{milestone_id}/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    milestone_id: UUID,
    payload: TaskCreate,
    _owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    task_service: TaskService = Depends(get_task_service),
):
    task = task_service.create_task(
        milestone_id=milestone_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        assignee_id=payload.assignee_id,
        assignee_guest_id=payload.assignee_guest_id,
        due_date=payload.due_date,
    )
    return TaskRead.model_validate(task)


@router.get("/milestones/{milestone_id}/tasks", response_model=list[TaskRead])
def list_tasks(
    milestone_id: UUID,
    _actor: Actor = Depends(require_project_access_for_milestone()),
    task_service: TaskService = Depends(get_task_service),
):
    """Open to guests too (full task/plan-progress visibility is part of the
    guest dashboard, not just their own assigned tasks) - also closes the
    pre-existing gap where this used to accept any authenticated user
    regardless of project membership."""
    return [TaskRead.model_validate(t) for t in task_service.list_tasks(milestone_id)]


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id: UUID,
    _actor: Actor = Depends(require_project_access_for_task()),
    task_service: TaskService = Depends(get_task_service),
):
    try:
        return TaskRead.model_validate(task_service.get_task(task_id))
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/tasks/{task_id}/status", response_model=TaskRead)
def update_task_status(
    task_id: UUID,
    payload: TaskStatusUpdate,
    background_tasks: BackgroundTasks,
    actor: Actor = Depends(require_project_access_for_task()),
    task_service: TaskService = Depends(get_task_service),
    session_factory=Depends(get_session_factory),
    risk_orchestrator: RiskAnalysisOrchestratorPort = Depends(get_risk_orchestrator),
    activity_service: ActivityService = Depends(get_activity_service),
    db: Session = Depends(get_db),
):
    """Status-only update, reachable by guests (restricted to a task
    actually assigned to them - see update_status_as_guest) as well as real
    project members/owners (who already have this same permission via the
    full PATCH /tasks/{task_id}; this is just a narrower, guest-safe alias
    of that, not a privilege escalation for either actor kind)."""
    try:
        previous_status = task_service.get_task(task_id).status
        if actor.kind == "guest":
            task = task_service.update_status_as_guest(task_id, actor.guest.id, payload.status)
        else:
            task = task_service.update_task(task_id, status=payload.status)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotTaskAssigneeError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    if (
        actor.kind == "user"
        and previous_status != TaskStatus.DONE
        and task.status == TaskStatus.DONE
    ):
        project_id = _resolve_project_id(db, task_id=task.id)
        if project_id is not None:
            activity_service.log_task_completed(project_id, actor.user, task.title)

    background_tasks.add_task(
        run_immediate_risk_check, session_factory, risk_orchestrator, task_id=task.id
    )

    return TaskRead.model_validate(task)


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
    session_factory=Depends(get_session_factory),
    risk_orchestrator: RiskAnalysisOrchestratorPort = Depends(get_risk_orchestrator),
    activity_service: ActivityService = Depends(get_activity_service),
    db: Session = Depends(get_db),
):
    try:
        previous_status = task_service.get_task(task_id).status
        task = task_service.update_task(task_id, **payload.model_dump(exclude_unset=True))
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if previous_status != TaskStatus.DONE and task.status == TaskStatus.DONE:
        project_id = _resolve_project_id(db, task_id=task.id)
        if project_id is not None:
            activity_service.log_task_completed(project_id, current_user, task.title)

    # Task completion, a status change, or a due-date change can all move the
    # needle on the project's risk picture - check immediately rather than
    # waiting for the next 30-minute scheduler tick. compute_signals is free
    # and the risk cache already gates the one thing that costs money (the
    # Gemini call), so this fires unconditionally rather than special-casing
    # which fields changed.
    background_tasks.add_task(
        run_immediate_risk_check, session_factory, risk_orchestrator, task_id=task.id
    )

    return TaskRead.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: UUID,
    _owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    task_service: TaskService = Depends(get_task_service),
):
    task_service.delete_task(task_id)
