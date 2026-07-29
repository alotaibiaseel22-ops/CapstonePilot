import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status

from app.api.schemas.job import JobCreated
from app.api.v1.deps import (
    get_agent_run_repository,
    get_planning_orchestrator,
    get_project_service,
    get_proposal_analysis_service,
    get_risk_orchestrator,
    get_session_factory,
    require_role,
)
from app.application.ports.agent_run_repository import AgentRunRepository
from app.application.ports.planning_orchestrator import PlanningOrchestratorPort
from app.application.ports.risk_orchestrator import RiskAnalysisOrchestratorPort
from app.application.services.orchestrator_service import run_planning_job
from app.application.services.project_service import ProjectNotFoundError, ProjectService
from app.application.services.proposal_analysis_service import (
    FileTooLargeError,
    ProposalAnalysisService,
    UnsupportedFileTypeError,
)
from app.domain.entities import AgentRun, User
from app.domain.enums import AgentRunStatus, UserRole

router = APIRouter(tags=["proposals"])


@router.post(
    "/projects/{project_id}/plan/generate",
    response_model=JobCreated,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_plan(
    project_id: uuid.UUID,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    _owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    project_service: ProjectService = Depends(get_project_service),
    analysis_service: ProposalAnalysisService = Depends(get_proposal_analysis_service),
    agent_runs: AgentRunRepository = Depends(get_agent_run_repository),
    orchestrator: PlanningOrchestratorPort = Depends(get_planning_orchestrator),
    risk_orchestrator: RiskAnalysisOrchestratorPort = Depends(get_risk_orchestrator),
    session_factory=Depends(get_session_factory),
):
    try:
        project = project_service.get_project(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    content = await file.read()
    try:
        result = analysis_service.analyze(file.filename, content)
    except (UnsupportedFileTypeError, FileTooLargeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    # `content` is never written to disk or the DB. The extracted `text` lives
    # only in this request's memory and the AgentRun.input_ref below records
    # metadata about it (filename, length), never the text itself - it's handed
    # directly to the background job as a function argument, not persisted.

    now = datetime.now(UTC)
    agent_run = agent_runs.create(
        AgentRun(
            id=uuid.uuid4(),
            project_id=project_id,
            agent_type="planner",
            status=AgentRunStatus.QUEUED,
            input_ref={
                "filename": file.filename,
                "characters_extracted": result.characters_extracted,
            },
            output_ref=None,
            error=None,
            created_at=now,
            updated_at=now,
        )
    )

    background_tasks.add_task(
        run_planning_job,
        agent_run.id,
        project_id,
        project.name,
        project.description,
        result.text,
        session_factory,
        orchestrator,
        risk_orchestrator,
    )

    return JobCreated(job_id=agent_run.id)
