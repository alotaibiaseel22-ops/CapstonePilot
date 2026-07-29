from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas.recommendation import RecommendationRead
from app.api.v1.deps import get_activity_service, get_current_user, get_recommendation_service
from app.application.services.activity_service import ActivityService
from app.application.services.recommendation_service import (
    InvalidRecommendationStatusError,
    NotProjectOwnerError,
    ProjectNotFoundError,
    RecommendationNotFoundError,
    RecommendationService,
)
from app.domain.entities import User

router = APIRouter(tags=["recommendations"])


@router.get("/projects/{project_id}/recommendations", response_model=list[RecommendationRead])
def list_recommendations(
    project_id: UUID,
    _current_user: User = Depends(get_current_user),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    return recommendation_service.list_recommendations(project_id)


@router.post("/recommendations/{recommendation_id}/approve", response_model=RecommendationRead)
def approve_recommendation(
    recommendation_id: UUID,
    current_user: User = Depends(get_current_user),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
    activity_service: ActivityService = Depends(get_activity_service),
):
    try:
        recommendation = recommendation_service.approve_recommendation(
            recommendation_id, current_user.id
        )
    except (ProjectNotFoundError, RecommendationNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotProjectOwnerError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InvalidRecommendationStatusError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    activity_service.log_recommendation_approved(
        recommendation.project_id, current_user, recommendation.title
    )
    return recommendation


@router.post("/recommendations/{recommendation_id}/reject", response_model=RecommendationRead)
def reject_recommendation(
    recommendation_id: UUID,
    current_user: User = Depends(get_current_user),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
    activity_service: ActivityService = Depends(get_activity_service),
):
    try:
        recommendation = recommendation_service.reject_recommendation(
            recommendation_id, current_user.id
        )
    except (ProjectNotFoundError, RecommendationNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotProjectOwnerError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InvalidRecommendationStatusError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    activity_service.log_recommendation_rejected(
        recommendation.project_id, current_user, recommendation.title
    )
    return recommendation
