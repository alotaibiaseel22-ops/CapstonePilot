from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.api.schemas.auth import UserRead
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
    inviter_name: str
    email: str | None
    user_exists: bool
    is_valid: bool


class InvitationOnboardRequest(BaseModel):
    name: str = Field(min_length=1)


class InvitationOnboardResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
    project_id: UUID
