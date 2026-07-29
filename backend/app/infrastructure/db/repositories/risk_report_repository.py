from uuid import UUID

from sqlalchemy.orm import Session

from app.application.ports.risk_report_repository import RiskReportRepository
from app.domain.entities import RiskReport
from app.domain.enums import RiskSeverity
from app.infrastructure.db.models import RiskReportModel


def _to_entity(model: RiskReportModel) -> RiskReport:
    return RiskReport(
        id=model.id,
        project_id=model.project_id,
        plan_version=model.plan_version,
        severity=RiskSeverity(model.severity),
        category=model.category,
        title=model.title,
        description=model.description,
        created_at=model.created_at,
    )


class SqlAlchemyRiskReportRepository(RiskReportRepository):
    def __init__(self, session: Session):
        self._session = session

    def create(self, risk_report: RiskReport) -> RiskReport:
        model = RiskReportModel(
            id=risk_report.id,
            project_id=risk_report.project_id,
            plan_version=risk_report.plan_version,
            severity=risk_report.severity.value,
            category=risk_report.category,
            title=risk_report.title,
            description=risk_report.description,
            created_at=risk_report.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def list_by_project(self, project_id: UUID) -> list[RiskReport]:
        query = (
            self._session.query(RiskReportModel)
            .filter(RiskReportModel.project_id == project_id)
            .order_by(RiskReportModel.created_at.desc())
        )
        return [_to_entity(model) for model in query.all()]

    def delete_by_project(self, project_id: UUID) -> None:
        query = self._session.query(RiskReportModel).filter(
            RiskReportModel.project_id == project_id
        )
        for model in query.all():
            self._session.delete(model)
        self._session.commit()
