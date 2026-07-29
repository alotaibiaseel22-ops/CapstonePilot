from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobCreated(BaseModel):
    job_id: UUID


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    agent_type: str
    status: str
    output_ref: dict[str, Any] | None
    error: str | None
    created_at: datetime
    updated_at: datetime
