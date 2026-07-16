from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import Project


class ProjectRepository(ABC):
    @abstractmethod
    def get_by_id(self, project_id: UUID) -> Project | None: ...

    @abstractmethod
    def list_all(self) -> list[Project]: ...

    @abstractmethod
    def create(self, project: Project) -> Project: ...

    @abstractmethod
    def update(self, project: Project) -> Project: ...

    @abstractmethod
    def delete(self, project_id: UUID) -> None: ...
