from uuid import UUID

from app.application.ports.risk_report_repository import RiskReportRepository
from app.domain.entities import RiskReport


class RiskService:
    def __init__(self, risk_report_repository: RiskReportRepository):
        self._risks = risk_report_repository

    def list_risks(self, project_id: UUID) -> list[RiskReport]:
        return self._risks.list_by_project(project_id)
