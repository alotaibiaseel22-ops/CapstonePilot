from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import Document


class DocumentRepository(ABC):
    @abstractmethod
    def get_by_id(self, document_id: UUID) -> Document | None: ...

    @abstractmethod
    def list_by_project(self, project_id: UUID) -> list[Document]: ...

    @abstractmethod
    def create(self, document: Document) -> Document: ...

    @abstractmethod
    def delete(self, document_id: UUID) -> None: ...
