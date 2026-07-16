from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import Task


class TaskRepository(ABC):
    @abstractmethod
    def get_by_id(self, task_id: UUID) -> Task | None: ...

    @abstractmethod
    def list_by_milestone(self, milestone_id: UUID) -> list[Task]: ...

    @abstractmethod
    def create(self, task: Task) -> Task: ...

    @abstractmethod
    def update(self, task: Task) -> Task: ...

    @abstractmethod
    def delete(self, task_id: UUID) -> None: ...
