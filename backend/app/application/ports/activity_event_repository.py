from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.entities import ActivityEvent


class ActivityEventRepository(ABC):
    @abstractmethod
    def create(self, event: ActivityEvent) -> ActivityEvent: ...

    @abstractmethod
    def list_by_project(self, project_id: UUID, limit: int = 20) -> list[ActivityEvent]: ...

    @abstractmethod
    def count_since(self, project_ids: list[UUID], since: datetime | None) -> int: ...

    @abstractmethod
    def delete_by_project(self, project_id: UUID) -> None: ...
