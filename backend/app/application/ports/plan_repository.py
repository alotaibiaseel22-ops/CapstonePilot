from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import Plan


class PlanRepository(ABC):
    """Covers project-creation's empty draft Plan (ProjectService) and the
    Planner's draft->proposed->approved/draft transitions (PlanService, Iteration 10).
    Multi-version replanning (superseding an approved plan with a new draft)
    is still deferred to the Risk/Recommendation iterations.
    """

    @abstractmethod
    def create(self, plan: Plan) -> Plan: ...

    @abstractmethod
    def update(self, plan: Plan) -> Plan: ...

    @abstractmethod
    def get_by_id(self, plan_id: UUID) -> Plan | None: ...

    @abstractmethod
    def get_current_for_project(self, project_id: UUID) -> Plan | None: ...

    @abstractmethod
    def list_by_project(self, project_id: UUID) -> list[Plan]: ...

    @abstractmethod
    def delete(self, plan_id: UUID) -> None: ...
