from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.enums import Language


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    detected_language: Language | None
    uploaded_by: UUID
    created_at: datetime
