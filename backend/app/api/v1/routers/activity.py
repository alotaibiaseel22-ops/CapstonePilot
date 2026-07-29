from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.schemas.activity_event import ActivityEventRead
from app.api.v1.deps import get_activity_service, get_current_user
from app.application.services.activity_service import ActivityService
from app.domain.entities import User

router = APIRouter(tags=["activity"])


@router.get("/projects/{project_id}/activity", response_model=list[ActivityEventRead])
def list_project_activity(
    project_id: UUID,
    _current_user: User = Depends(get_current_user),
    activity_service: ActivityService = Depends(get_activity_service),
):
    return activity_service.list_project_activity(project_id)
