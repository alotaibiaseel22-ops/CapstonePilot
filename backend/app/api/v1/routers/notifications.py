from fastapi import APIRouter, Depends

from app.api.schemas.activity_event import UnreadCountRead
from app.api.v1.deps import get_activity_service, get_current_user
from app.application.services.activity_service import ActivityService
from app.domain.entities import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/unread-count", response_model=UnreadCountRead)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    activity_service: ActivityService = Depends(get_activity_service),
):
    return UnreadCountRead(count=activity_service.get_unread_count(current_user))


@router.post("/mark-seen", response_model=UnreadCountRead)
def mark_seen(
    current_user: User = Depends(get_current_user),
    activity_service: ActivityService = Depends(get_activity_service),
):
    activity_service.mark_seen(current_user)
    return UnreadCountRead(count=0)
