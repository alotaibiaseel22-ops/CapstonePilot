from collections.abc import Callable, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.application.ports.agent_run_repository import AgentRunRepository
from app.application.ports.email_service import EmailService
from app.application.ports.planning_orchestrator import PlanningOrchestratorPort
from app.application.ports.risk_orchestrator import RiskAnalysisOrchestratorPort
from app.application.ports.user_repository import UserRepository
from app.application.services.activity_service import ActivityService
from app.application.services.auth_service import AuthService
from app.application.services.invitation_service import InvitationService
from app.application.services.milestone_service import MilestoneService
from app.application.services.plan_service import PlanService
from app.application.services.project_member_service import ProjectMemberService
from app.application.services.project_service import ProjectService
from app.application.services.proposal_analysis_service import ProposalAnalysisService
from app.application.services.recommendation_service import RecommendationService
from app.application.services.risk_service import RiskService
from app.application.services.task_service import TaskService
from app.core.config import settings
from app.domain.entities import User
from app.domain.enums import UserRole
from app.infrastructure.db.repositories.activity_event_repository import (
    SqlAlchemyActivityEventRepository,
)
from app.infrastructure.db.repositories.agent_run_repository import SqlAlchemyAgentRunRepository
from app.infrastructure.db.repositories.invitation_repository import SqlAlchemyInvitationRepository
from app.infrastructure.db.repositories.milestone_repository import SqlAlchemyMilestoneRepository
from app.infrastructure.db.repositories.plan_repository import SqlAlchemyPlanRepository
from app.infrastructure.db.repositories.project_member_repository import (
    SqlAlchemyProjectMemberRepository,
)
from app.infrastructure.db.repositories.project_repository import SqlAlchemyProjectRepository
from app.infrastructure.db.repositories.recommendation_repository import (
    SqlAlchemyRecommendationRepository,
)
from app.infrastructure.db.repositories.risk_report_repository import SqlAlchemyRiskReportRepository
from app.infrastructure.db.repositories.task_repository import SqlAlchemyTaskRepository
from app.infrastructure.db.repositories.user_repository import SqlAlchemyUserRepository
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.email.email_service import build_email_service
from app.infrastructure.security.jwt import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(SqlAlchemyUserRepository(db))


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return SqlAlchemyUserRepository(db)


def get_email_service() -> EmailService:
    return build_email_service()


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    return ProjectService(
        SqlAlchemyProjectRepository(db),
        SqlAlchemyPlanRepository(db),
        SqlAlchemyProjectMemberRepository(db),
        SqlAlchemyInvitationRepository(db),
        SqlAlchemyMilestoneRepository(db),
        SqlAlchemyTaskRepository(db),
        SqlAlchemyRiskReportRepository(db),
        SqlAlchemyRecommendationRepository(db),
        SqlAlchemyActivityEventRepository(db),
        SqlAlchemyAgentRunRepository(db),
    )


def get_activity_service(db: Session = Depends(get_db)) -> ActivityService:
    return ActivityService(
        SqlAlchemyActivityEventRepository(db),
        SqlAlchemyProjectRepository(db),
        SqlAlchemyProjectMemberRepository(db),
        SqlAlchemyUserRepository(db),
    )


def get_project_member_service(db: Session = Depends(get_db)) -> ProjectMemberService:
    return ProjectMemberService(
        SqlAlchemyProjectMemberRepository(db),
        SqlAlchemyUserRepository(db),
        SqlAlchemyProjectRepository(db),
    )


def get_invitation_service(
    db: Session = Depends(get_db), email_service: EmailService = Depends(get_email_service)
) -> InvitationService:
    return InvitationService(
        SqlAlchemyInvitationRepository(db),
        SqlAlchemyProjectMemberRepository(db),
        SqlAlchemyUserRepository(db),
        SqlAlchemyProjectRepository(db),
        email_service,
    )


def get_proposal_analysis_service() -> ProposalAnalysisService:
    return ProposalAnalysisService()


def get_milestone_service(db: Session = Depends(get_db)) -> MilestoneService:
    return MilestoneService(SqlAlchemyMilestoneRepository(db), SqlAlchemyPlanRepository(db))


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    return TaskService(SqlAlchemyTaskRepository(db))


def get_agent_run_repository(db: Session = Depends(get_db)) -> AgentRunRepository:
    return SqlAlchemyAgentRunRepository(db)


def get_plan_service(db: Session = Depends(get_db)) -> PlanService:
    return PlanService(
        SqlAlchemyPlanRepository(db),
        SqlAlchemyProjectRepository(db),
        SqlAlchemyMilestoneRepository(db),
        SqlAlchemyTaskRepository(db),
    )


def get_session_factory() -> Callable[[], Session]:
    """Used by the plan/generate route to hand BackgroundTasks a way to open its
    OWN db session later, since the request's session is closed by the time a
    background task runs. Overridden in tests to point at the test DB."""
    return SessionLocal


def get_planning_orchestrator() -> PlanningOrchestratorPort:
    """Real CrewAI implementation when a key is configured, otherwise a
    deterministic placeholder - same fallback shape as get_email_service.
    The crewai-backed import is deliberately deferred to inside this branch so
    that booting the app (or running with no key at all) never pays crewai's
    import cost, which is the whole point of the fake being a *lightweight*
    fallback."""
    if settings.GEMINI_API_KEY:
        from app.infrastructure.agents.crewai_planning_orchestrator import (
            CrewAIPlanningOrchestrator,
        )

        return CrewAIPlanningOrchestrator()

    from app.infrastructure.agents.fake_planning_orchestrator import FakePlanningOrchestrator

    return FakePlanningOrchestrator()


def get_risk_service(db: Session = Depends(get_db)) -> RiskService:
    return RiskService(SqlAlchemyRiskReportRepository(db))


def get_recommendation_service(db: Session = Depends(get_db)) -> RecommendationService:
    return RecommendationService(
        SqlAlchemyRecommendationRepository(db), SqlAlchemyProjectRepository(db)
    )


def get_risk_orchestrator() -> RiskAnalysisOrchestratorPort:
    """Same key-presence branch as get_planning_orchestrator, same deferred
    crewai-backed import so booting with no key never pays crewai's import
    cost."""
    if settings.GEMINI_API_KEY:
        from app.infrastructure.agents.crewai_risk_orchestrator import CrewAIRiskOrchestrator

        return CrewAIRiskOrchestrator()

    from app.infrastructure.agents.fake_risk_orchestrator import FakeRiskOrchestrator

    return FakeRiskOrchestrator()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_error

    user = SqlAlchemyUserRepository(db).get_by_id(user_id)
    if user is None:
        raise credentials_error
    return user


def require_role(role: UserRole):
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires the '{role.value}' role",
            )
        return current_user

    return _check
