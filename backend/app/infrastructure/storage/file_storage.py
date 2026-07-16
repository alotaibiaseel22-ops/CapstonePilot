import uuid
from pathlib import Path
from uuid import UUID

from app.application.ports.file_storage import FileStorage
from app.core.config import settings


class LocalFileStorage(FileStorage):
    """Local-disk adapter. Swappable later for an object-storage (S3-style) adapter
    behind the same FileStorage port without touching DocumentService."""

    def __init__(self, base_dir: str | None = None):
        self._base_dir = Path(base_dir or settings.UPLOAD_DIR)

    def save(self, project_id: UUID, filename: str, content: bytes) -> str:
        project_dir = self._base_dir / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)

        suffix = Path(filename).suffix
        stored_name = f"{uuid.uuid4()}{suffix}"
        destination = project_dir / stored_name
        destination.write_bytes(content)

        return str(destination.as_posix())

    def delete(self, storage_path: str) -> None:
        path = Path(storage_path)
        if path.exists():
            path.unlink()
