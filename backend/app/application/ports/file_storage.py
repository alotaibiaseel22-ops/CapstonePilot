from abc import ABC, abstractmethod
from uuid import UUID


class FileStorage(ABC):
    @abstractmethod
    def save(self, project_id: UUID, filename: str, content: bytes) -> str:
        """Persist file content and return a storage_path that later identifies it."""
        ...

    @abstractmethod
    def delete(self, storage_path: str) -> None: ...
