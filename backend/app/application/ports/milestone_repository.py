from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import Milestone


class MilestoneRepository(ABC):
    @abstractmethod
    def get_by_id(self, milestone_id: UUID) -> Milestone | None: ...

    @abstractmethod
    def list_by_plan(self, plan_id: UUID) -> list[Milestone]: ...

    @abstractmethod
    def create(self, milestone: Milestone) -> Milestone: ...

    @abstractmethod
    def update(self, milestone: Milestone) -> Milestone: ...

    @abstractmethod
    def delete(self, milestone_id: UUID) -> None: ...
