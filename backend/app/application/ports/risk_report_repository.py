from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import RiskReport


class RiskReportRepository(ABC):
    @abstractmethod
    def create(self, risk_report: RiskReport) -> RiskReport: ...

    @abstractmethod
    def list_by_project(self, project_id: UUID) -> list[RiskReport]: ...

    @abstractmethod
    def delete_by_project(self, project_id: UUID) -> None: ...
