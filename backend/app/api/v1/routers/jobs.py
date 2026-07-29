from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas.job import JobRead
from app.api.v1.deps import get_agent_run_repository, get_current_user, get_project_service
from app.application.ports.agent_run_repository import AgentRunRepository
from app.application.services.project_service import (
    NotProjectOwnerError,
    ProjectNotFoundError,
    ProjectService,
)
from app.domain.entities import User

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=JobRead)
def get_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    agent_runs: AgentRunRepository = Depends(get_agent_run_repository),
    project_service: ProjectService = Depends(get_project_service),
):
    agent_run = agent_runs.get_by_id(job_id)
    if agent_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found")
    try:
        project_service.assert_owner(agent_run.project_id, current_user.id)
    except NotProjectOwnerError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return JobRead.model_validate(agent_run)
