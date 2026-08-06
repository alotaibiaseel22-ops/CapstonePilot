from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    uploader_id: UUID | None
    uploader_guest_id: UUID | None
    created_at: datetime
