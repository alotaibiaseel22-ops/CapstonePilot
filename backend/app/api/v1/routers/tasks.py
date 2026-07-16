from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.api.v1.deps import get_current_user, get_task_service, require_role
from app.application.services.task_service import TaskNotFoundError, TaskService
from app.domain.entities import User
from app.domain.enums import UserRole

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
        due_date=payload.due_date,
    )
    return TaskRead.model_validate(task)


@router.get("/milestones/{milestone_id}/tasks", response_model=list[TaskRead])
def list_tasks(
    milestone_id: UUID,
    _current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return [TaskRead.model_validate(t) for t in task_service.list_tasks(milestone_id)]


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id: UUID,
    _current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    try:
        return TaskRead.model_validate(task_service.get_task(task_id))
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    _current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    try:
        task = task_service.update_task(task_id, **payload.model_dump(exclude_unset=True))
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return TaskRead.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: UUID,
    _owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    task_service: TaskService = Depends(get_task_service),
):
    task_service.delete_task(task_id)
