from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.ports.activity_event_repository import ActivityEventRepository
from app.domain.entities import ActivityEvent
from app.infrastructure.db.models import ActivityEventModel


def _to_entity(model: ActivityEventModel) -> ActivityEvent:
    return ActivityEvent(
        id=model.id,
        project_id=model.project_id,
        actor_id=model.actor_id,
        event_type=model.event_type,
        message=model.message,
        created_at=model.created_at,
    )


class SqlAlchemyActivityEventRepository(ActivityEventRepository):
    def __init__(self, session: Session):
        self._session = session

    def create(self, event: ActivityEvent) -> ActivityEvent:
        model = ActivityEventModel(
            id=event.id,
            project_id=event.project_id,
            actor_id=event.actor_id,
            event_type=event.event_type,
            message=event.message,
            created_at=event.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def list_by_project(self, project_id: UUID, limit: int = 20) -> list[ActivityEvent]:
        query = (
            self._session.query(ActivityEventModel)
            .filter(ActivityEventModel.project_id == project_id)
            .order_by(ActivityEventModel.created_at.desc())
            .limit(limit)
        )
        return [_to_entity(model) for model in query.all()]

    def count_since(self, project_ids: list[UUID], since: datetime | None) -> int:
        if not project_ids:
            return 0
        query = self._session.query(ActivityEventModel).filter(
            ActivityEventModel.project_id.in_(project_ids)
        )
        if since is not None:
            query = query.filter(ActivityEventModel.created_at > since)
        return query.count()

    def delete_by_project(self, project_id: UUID) -> None:
        query = self._session.query(ActivityEventModel).filter(
            ActivityEventModel.project_id == project_id
        )
        for model in query.all():
            self._session.delete(model)
        self._session.commit()
