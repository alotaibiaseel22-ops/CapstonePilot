from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.api.schemas.proposal import ProposalAnalysisRead
from app.api.v1.deps import get_project_service, get_proposal_analysis_service, require_role
from app.application.services.project_service import ProjectNotFoundError, ProjectService
from app.application.services.proposal_analysis_service import (
    FileTooLargeError,
    ProposalAnalysisService,
    UnsupportedFileTypeError,
)
from app.domain.entities import User
from app.domain.enums import UserRole

router = APIRouter(tags=["proposals"])


@router.post("/projects/{project_id}/analyze-proposal", response_model=ProposalAnalysisRead)
async def analyze_proposal(
    project_id: UUID,
    file: UploadFile,
    _owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    project_service: ProjectService = Depends(get_project_service),
    analysis_service: ProposalAnalysisService = Depends(get_proposal_analysis_service),
):
    try:
        project_service.get_project(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    content = await file.read()
    try:
        result = analysis_service.analyze(file.filename, content)
    except (UnsupportedFileTypeError, FileTooLargeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    # `content` is never written to disk or the DB - it goes out of scope here.
    return ProposalAnalysisRead(
        message=result.message,
        characters_extracted=result.characters_extracted,
        preview=result.preview,
    )
