from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import Attachment


class AttachmentRepository(ABC):
    @abstractmethod
    def create(self, attachment: Attachment, content: bytes) -> Attachment: ...

    @abstractmethod
    def get_by_id(self, attachment_id: UUID) -> Attachment | None: ...

    @abstractmethod
    def get_content(self, attachment_id: UUID) -> bytes | None: ...

    @abstractmethod
    def list_by_project(self, project_id: UUID) -> list[Attachment]: ...

    @abstractmethod
    def delete(self, attachment_id: UUID) -> None: ...
