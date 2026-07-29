from uuid import UUID

from sqlalchemy.orm import Session

from app.application.ports.recommendation_repository import RecommendationRepository
from app.domain.entities import Recommendation
from app.domain.enums import RecommendationStatus
from app.infrastructure.db.models import RecommendationModel


def _to_entity(model: RecommendationModel) -> Recommendation:
    return Recommendation(
        id=model.id,
        risk_report_id=model.risk_report_id,
        project_id=model.project_id,
        title=model.title,
        category=model.category,
        severity=model.severity,
        effort=model.effort,
        impact=model.impact,
        description=model.description,
        rationale=model.rationale,
        proposed_changes=model.proposed_changes,
        status=RecommendationStatus(model.status),
        created_at=model.created_at,
    )


class SqlAlchemyRecommendationRepository(RecommendationRepository):
    def __init__(self, session: Session):
        self._session = session

    def create(self, recommendation: Recommendation) -> Recommendation:
        model = RecommendationModel(
            id=recommendation.id,
            risk_report_id=recommendation.risk_report_id,
            project_id=recommendation.project_id,
            title=recommendation.title,
            category=recommendation.category,
            severity=recommendation.severity,
            effort=recommendation.effort,
            impact=recommendation.impact,
            description=recommendation.description,
            rationale=recommendation.rationale,
            proposed_changes=recommendation.proposed_changes,
            status=recommendation.status.value,
            created_at=recommendation.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def list_by_project(self, project_id: UUID) -> list[Recommendation]:
        query = (
            self._session.query(RecommendationModel)
            .filter(RecommendationModel.project_id == project_id)
            .order_by(RecommendationModel.created_at.desc())
        )
        return [_to_entity(model) for model in query.all()]

    def get_by_id(self, recommendation_id: UUID) -> Recommendation | None:
        model = self._session.get(RecommendationModel, recommendation_id)
        return _to_entity(model) if model else None

    def update(self, recommendation: Recommendation) -> Recommendation:
        model = self._session.get(RecommendationModel, recommendation.id)
        if model is None:
            raise ValueError(f"Recommendation {recommendation.id} not found")
        model.status = recommendation.status.value
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def delete_by_project(self, project_id: UUID) -> None:
        query = self._session.query(RecommendationModel).filter(
            RecommendationModel.project_id == project_id
        )
        for model in query.all():
            self._session.delete(model)
        self._session.commit()
