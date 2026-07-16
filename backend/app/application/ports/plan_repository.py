from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import Plan


class PlanRepository(ABC):
    """Minimal port: full Plan CRUD/versioning ships with the orchestrator (Iterations 10-13).

    For now this only supports what ProjectService needs internally to give every
    new project a Plan row for Milestones to attach to, per the ERD in the
    architecture doc (Project -> Plan -> Milestone -> Task).
    """

    @abstractmethod
    def create(self, plan: Plan) -> Plan: ...

    @abstractmethod
    def get_by_id(self, plan_id: UUID) -> Plan | None: ...

    @abstractmethod
    def get_current_for_project(self, project_id: UUID) -> Plan | None: ...
