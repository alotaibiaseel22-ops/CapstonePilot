from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.domain.entities import AgentRun
from app.domain.enums import AgentRunStatus


class AgentRunRepository(ABC):
    @abstractmethod
    def get_by_id(self, agent_run_id: UUID) -> AgentRun | None: ...

    @abstractmethod
    def create(self, agent_run: AgentRun) -> AgentRun: ...

    @abstractmethod
    def update_status(
        self,
        agent_run_id: UUID,
        status: AgentRunStatus,
        output_ref: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> AgentRun: ...
