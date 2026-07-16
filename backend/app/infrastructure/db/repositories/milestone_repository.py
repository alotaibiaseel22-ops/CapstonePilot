from uuid import UUID

from sqlalchemy.orm import Session

from app.application.ports.milestone_repository import MilestoneRepository
from app.domain.entities import Milestone
from app.infrastructure.db.models import MilestoneModel


def _to_entity(model: MilestoneModel) -> Milestone:
    return Milestone(
        id=model.id,
        plan_id=model.plan_id,
        title=model.title,
        due_date=model.due_date,
        order=model.order,
        created_at=model.created_at,
    )


class SqlAlchemyMilestoneRepository(MilestoneRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, milestone_id: UUID) -> Milestone | None:
        model = self._session.get(MilestoneModel, milestone_id)
        return _to_entity(model) if model else None

    def list_by_plan(self, plan_id: UUID) -> list[Milestone]:
        return [
            _to_entity(model)
            for model in self._session.query(MilestoneModel)
            .filter(MilestoneModel.plan_id == plan_id)
            .order_by(MilestoneModel.order)
            .all()
        ]

    def create(self, milestone: Milestone) -> Milestone:
        model = MilestoneModel(
            id=milestone.id,
            plan_id=milestone.plan_id,
            title=milestone.title,
            due_date=milestone.due_date,
            order=milestone.order,
            created_at=milestone.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def update(self, milestone: Milestone) -> Milestone:
        model = self._session.get(MilestoneModel, milestone.id)
        if model is None:
            raise ValueError(f"Milestone {milestone.id} not found")
        model.title = milestone.title
        model.due_date = milestone.due_date
        model.order = milestone.order
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def delete(self, milestone_id: UUID) -> None:
        model = self._session.get(MilestoneModel, milestone_id)
        if model is not None:
            self._session.delete(model)
            self._session.commit()
