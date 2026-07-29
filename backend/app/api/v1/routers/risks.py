from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.schemas.risk_report import RiskReportRead
from app.api.v1.deps import get_current_user, get_risk_service
from app.application.services.risk_service import RiskService
from app.domain.entities import User

router = APIRouter(tags=["risks"])


@router.get("/projects/{project_id}/risks", response_model=list[RiskReportRead])
def list_risks(
    project_id: UUID,
    _current_user: User = Depends(get_current_user),
    risk_service: RiskService = Depends(get_risk_service),
):
    return risk_service.list_risks(project_id)
