from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import ProjectMember


class ProjectMemberRepository(ABC):
    @abstractmethod
    def add(self, member: ProjectMember) -> ProjectMember: ...

    @abstractmethod
    def list_by_project(self, project_id: UUID) -> list[ProjectMember]: ...

    @abstractmethod
    def exists(self, project_id: UUID, user_id: UUID) -> bool: ...

    @abstractmethod
    def remove(self, project_id: UUID, user_id: UUID) -> None: ...
