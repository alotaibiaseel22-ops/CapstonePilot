from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums import Language


@dataclass
class Document:
    id: UUID
    project_id: UUID
    filename: str
    storage_path: str
    content_type: str
    size_bytes: int
    detected_language: Language | None
    uploaded_by: UUID
    created_at: datetime
