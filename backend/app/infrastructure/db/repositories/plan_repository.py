from uuid import UUID

from sqlalchemy.orm import Session

from app.application.ports.plan_repository import PlanRepository
from app.domain.entities import Plan
from app.domain.enums import PlanStatus
from app.infrastructure.db.models import PlanModel


def _to_entity(model: PlanModel) -> Plan:
    return Plan(
        id=model.id,
        project_id=model.project_id,
        version=model.version,
        status=PlanStatus(model.status),
        rationale=model.rationale,
        created_at=model.created_at,
    )


class SqlAlchemyPlanRepository(PlanRepository):
    def __init__(self, session: Session):
        self._session = session

    def create(self, plan: Plan) -> Plan:
        model = PlanModel(
            id=plan.id,
            project_id=plan.project_id,
            version=plan.version,
            status=plan.status.value,
            rationale=plan.rationale,
            created_at=plan.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def update(self, plan: Plan) -> Plan:
        model = self._session.get(PlanModel, plan.id)
        if model is None:
            raise ValueError(f"Plan {plan.id} not found")
        model.status = plan.status.value
        model.rationale = plan.rationale
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def get_by_id(self, plan_id: UUID) -> Plan | None:
        model = self._session.get(PlanModel, plan_id)
        return _to_entity(model) if model else None

    def get_current_for_project(self, project_id: UUID) -> Plan | None:
        model = (
            self._session.query(PlanModel)
            .filter(PlanModel.project_id == project_id)
            .order_by(PlanModel.version.desc())
            .first()
        )
        return _to_entity(model) if model else None

    def list_by_project(self, project_id: UUID) -> list[Plan]:
        query = self._session.query(PlanModel).filter(PlanModel.project_id == project_id)
        return [_to_entity(model) for model in query.all()]

    def delete(self, plan_id: UUID) -> None:
        model = self._session.get(PlanModel, plan_id)
        if model is not None:
            self._session.delete(model)
            self._session.commit()
