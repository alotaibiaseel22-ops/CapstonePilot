from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import Comment


class CommentRepository(ABC):
    @abstractmethod
    def create(self, comment: Comment) -> Comment: ...

    @abstractmethod
    def get_by_id(self, comment_id: UUID) -> Comment | None: ...

    @abstractmethod
    def list_by_project(self, project_id: UUID) -> list[Comment]: ...

    @abstractmethod
    def delete(self, comment_id: UUID) -> None: ...
