from uuid import UUID

from app.application.ports.project_repository import ProjectRepository
from app.application.ports.recommendation_repository import RecommendationRepository
from app.domain.entities import Recommendation
from app.domain.enums import RecommendationStatus


class ProjectNotFoundError(Exception):
    pass


class NotProjectOwnerError(Exception):
    pass


class RecommendationNotFoundError(Exception):
    pass


class InvalidRecommendationStatusError(Exception):
    pass


class RecommendationService:
    def __init__(
        self,
        recommendation_repository: RecommendationRepository,
        project_repository: ProjectRepository,
    ):
        self._recommendations = recommendation_repository
        self._projects = project_repository

    def list_recommendations(self, project_id: UUID) -> list[Recommendation]:
        return self._recommendations.list_by_project(project_id)

    def _assert_owner(self, project_id: UUID, requesting_user_id: UUID) -> None:
        project = self._projects.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project {project_id} not found")
        if project.owner_id != requesting_user_id:
            raise NotProjectOwnerError("Only this project's owner can do that")

    def _set_status(
        self, recommendation_id: UUID, requesting_user_id: UUID, new_status: RecommendationStatus
    ) -> Recommendation:
        recommendation = self._recommendations.get_by_id(recommendation_id)
        if recommendation is None:
            raise RecommendationNotFoundError(f"Recommendation {recommendation_id} not found")
        self._assert_owner(recommendation.project_id, requesting_user_id)
        if recommendation.status != RecommendationStatus.PENDING:
            raise InvalidRecommendationStatusError(
                "Only a pending recommendation can be decided on"
            )
        recommendation.status = new_status
        return self._recommendations.update(recommendation)

    def approve_recommendation(
        self, recommendation_id: UUID, requesting_user_id: UUID
    ) -> Recommendation:
        return self._set_status(
            recommendation_id, requesting_user_id, RecommendationStatus.APPROVED
        )

    def reject_recommendation(
        self, recommendation_id: UUID, requesting_user_id: UUID
    ) -> Recommendation:
        return self._set_status(
            recommendation_id, requesting_user_id, RecommendationStatus.REJECTED
        )
