from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.enums import AgentRunStatus


@dataclass
class AgentRun:
    id: UUID
    project_id: UUID
    agent_type: str
    status: AgentRunStatus
    input_ref: dict[str, Any]
    output_ref: dict[str, Any] | None
    error: str | None
    created_at: datetime
    updated_at: datetime
