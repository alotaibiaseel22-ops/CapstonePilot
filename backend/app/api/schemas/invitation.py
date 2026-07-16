from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.domain.enums import InvitationStatus


class InvitationEmailCreate(BaseModel):
    emails: list[EmailStr]


class InvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    email: str | None
    token: str
    status: InvitationStatus
    created_at: datetime
    accepted_at: datetime | None
    expires_at: datetime | None


class InvitationAcceptResult(BaseModel):
    project_id: UUID


class InvitationPreviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_name: str
    email: str | None
    user_exists: bool
    is_valid: bool
