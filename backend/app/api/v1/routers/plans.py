from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas.plan import PlanRead
from app.api.v1.deps import get_activity_service, get_current_user, get_plan_service
from app.application.services.activity_service import ActivityService
from app.application.services.plan_service import (
    InvalidPlanStatusError,
    NotProjectOwnerError,
    PlanNotFoundError,
    PlanService,
    ProjectNotFoundError,
)
from app.domain.entities import User

router = APIRouter(tags=["plans"])


@router.get("/projects/{project_id}/plan", response_model=PlanRead)
def get_plan(
    project_id: UUID,
    _current_user: User = Depends(get_current_user),
    plan_service: PlanService = Depends(get_plan_service),
):
    try:
        return PlanRead.model_validate(plan_service.get_current_plan(project_id))
    except PlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/projects/{project_id}/plan/approve", response_model=PlanRead)
def approve_plan(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    plan_service: PlanService = Depends(get_plan_service),
    activity_service: ActivityService = Depends(get_activity_service),
):
    try:
        plan = plan_service.approve_plan(project_id, current_user.id)
    except (ProjectNotFoundError, PlanNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotProjectOwnerError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InvalidPlanStatusError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    activity_service.log_plan_approved(project_id, current_user)
    return PlanRead.model_validate(plan)


@router.post("/projects/{project_id}/plan/reject", response_model=PlanRead)
def reject_plan(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    plan_service: PlanService = Depends(get_plan_service),
    activity_service: ActivityService = Depends(get_activity_service),
):
    try:
        plan = plan_service.reject_plan(project_id, current_user.id)
    except (ProjectNotFoundError, PlanNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotProjectOwnerError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InvalidPlanStatusError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    activity_service.log_plan_rejected(project_id, current_user)
    return PlanRead.model_validate(plan)
