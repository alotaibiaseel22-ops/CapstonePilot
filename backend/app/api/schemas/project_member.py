from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class ProjectMemberAdd(BaseModel):
    email: EmailStr


class ProjectMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    name: str
    email: str
    role: str
    added_at: datetime
