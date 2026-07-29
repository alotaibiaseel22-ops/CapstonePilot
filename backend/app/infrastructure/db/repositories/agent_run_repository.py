from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.ports.agent_run_repository import AgentRunRepository
from app.domain.entities import AgentRun
from app.domain.enums import AgentRunStatus
from app.infrastructure.db.models import AgentRunModel


def _to_entity(model: AgentRunModel) -> AgentRun:
    return AgentRun(
        id=model.id,
        project_id=model.project_id,
        agent_type=model.agent_type,
        status=AgentRunStatus(model.status),
        input_ref=model.input_ref,
        output_ref=model.output_ref,
        error=model.error,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyAgentRunRepository(AgentRunRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, agent_run_id: UUID) -> AgentRun | None:
        model = self._session.get(AgentRunModel, agent_run_id)
        return _to_entity(model) if model else None

    def create(self, agent_run: AgentRun) -> AgentRun:
        model = AgentRunModel(
            id=agent_run.id,
            project_id=agent_run.project_id,
            agent_type=agent_run.agent_type,
            status=agent_run.status.value,
            input_ref=agent_run.input_ref,
            output_ref=agent_run.output_ref,
            error=agent_run.error,
            created_at=agent_run.created_at,
            updated_at=agent_run.updated_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def update_status(
        self,
        agent_run_id: UUID,
        status: AgentRunStatus,
        output_ref: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> AgentRun:
        model = self._session.get(AgentRunModel, agent_run_id)
        if model is None:
            raise ValueError(f"AgentRun {agent_run_id} not found")
        model.status = status.value
        if output_ref is not None:
            model.output_ref = output_ref
        if error is not None:
            model.error = error
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)
