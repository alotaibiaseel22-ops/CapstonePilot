from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.application.ports.agent_run_repository import AgentRunRepository
from app.application.ports.email_service import EmailService
from app.application.ports.planning_orchestrator import PlanningOrchestratorPort
from app.application.ports.risk_orchestrator import RiskAnalysisOrchestratorPort
from app.application.ports.user_repository import UserRepository
from app.application.services.activity_service import ActivityService
from app.application.services.attachment_service import AttachmentService
from app.application.services.auth_service import AuthService
from app.application.services.comment_service import CommentService
from app.application.services.guest_service import (
    GuestAccessRevokedError,
    GuestNotFoundError,
    GuestService,
)
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
from app.domain.entities import Guest, User
from app.domain.enums import UserRole
from app.infrastructure.db.repositories.activity_event_repository import (
    SqlAlchemyActivityEventRepository,
)
from app.infrastructure.db.repositories.agent_run_repository import SqlAlchemyAgentRunRepository
from app.infrastructure.db.repositories.attachment_repository import (
    SqlAlchemyAttachmentRepository,
)
from app.infrastructure.db.repositories.comment_repository import SqlAlchemyCommentRepository
from app.infrastructure.db.repositories.guest_repository import SqlAlchemyGuestRepository
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
from app.infrastructure.scheduler import _resolve_project_id
from app.infrastructure.security.jwt import decode_access_token, decode_guest_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
# auto_error=False on both: get_current_actor needs to try a user token and
# then fall back to a guest token, so neither security scheme alone may
# short-circuit the request with its own 401 - get_current_actor raises the
# final 401 itself once both have been tried.
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)
guest_bearer_scheme = HTTPBearer(auto_error=False)


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


def get_guest_service(db: Session = Depends(get_db)) -> GuestService:
    return GuestService(SqlAlchemyGuestRepository(db), SqlAlchemyInvitationRepository(db))


def get_attachment_service(db: Session = Depends(get_db)) -> AttachmentService:
    return AttachmentService(SqlAlchemyAttachmentRepository(db))


def get_comment_service(db: Session = Depends(get_db)) -> CommentService:
    return CommentService(SqlAlchemyCommentRepository(db))


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
    if settings.GEMINI_API_KEYS:
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
    if settings.GEMINI_API_KEYS:
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


@dataclass
class Actor:
    """Either a real, fully-authenticated User (owner/collaborator) or a
    Guest (joined a shareable link, no account at all) - see the guest-access
    redesign. Exactly one of user/guest is set, matching kind."""

    kind: Literal["user", "guest"]
    user: User | None = None
    guest: Guest | None = None


def get_current_actor(
    token: str | None = Depends(oauth2_scheme_optional),
    guest_credentials: HTTPAuthorizationCredentials | None = Depends(guest_bearer_scheme),
    db: Session = Depends(get_db),
) -> Actor:
    """Tries a real user token first, then a guest token - safe to try both
    against the same Authorization header in sequence because the "scope"
    claim makes the two token shapes mutually exclusive (decode_access_token
    always rejects scope=="guest"; decode_guest_access_token always requires
    it), never ambiguous. require_role/get_current_user are untouched and
    used as-is everywhere else - this is only for the specific routes guests
    are permitted to reach (see require_project_access* below)."""
    if token:
        user_id = decode_access_token(token)
        if user_id is not None:
            user = SqlAlchemyUserRepository(db).get_by_id(user_id)
            if user is not None:
                return Actor(kind="user", user=user)

    if guest_credentials:
        payload = decode_guest_access_token(guest_credentials.credentials)
        if payload is not None:
            guest_service = GuestService(
                SqlAlchemyGuestRepository(db), SqlAlchemyInvitationRepository(db)
            )
            try:
                guest = guest_service.resolve_guest(payload.guest_id, payload.project_id)
                return Actor(kind="guest", guest=guest)
            except (GuestNotFoundError, GuestAccessRevokedError):
                pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _assert_actor_can_access_project(actor: Actor, project_id: UUID, db: Session) -> None:
    if actor.kind == "guest":
        if actor.guest.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This guest link does not grant access to this project",
            )
        return

    project = SqlAlchemyProjectRepository(db).get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    is_owner = project.owner_id == actor.user.id
    is_member = SqlAlchemyProjectMemberRepository(db).exists(project_id, actor.user.id)
    if not is_owner and not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this project"
        )


def require_project_access(project_id_param: str = "project_id"):
    """The one reusable dependency both real users and guests can satisfy.
    A user must own or be a member of this exact project_id; a guest's own
    token project_id must equal it - never grants anything on a different
    project. Also the correctly-scoped replacement for routes that used to
    only check Depends(get_current_user) with no membership check at all
    (e.g. GET /projects/{project_id})."""

    def _check(
        request: Request, actor: Actor = Depends(get_current_actor), db: Session = Depends(get_db)
    ) -> Actor:
        project_id = UUID(request.path_params[project_id_param])
        _assert_actor_can_access_project(actor, project_id, db)
        return actor

    return _check


def require_project_access_for_task():
    """Same as require_project_access, for routes keyed by task_id instead
    of project_id (no project_id in the URL) - walks task -> milestone ->
    plan -> project via scheduler.py's existing _resolve_project_id."""

    def _check(
        request: Request, actor: Actor = Depends(get_current_actor), db: Session = Depends(get_db)
    ) -> Actor:
        task_id = UUID(request.path_params["task_id"])
        project_id = _resolve_project_id(db, task_id=task_id)
        if project_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        _assert_actor_can_access_project(actor, project_id, db)
        return actor

    return _check


def require_project_access_for_milestone():
    """Same as require_project_access_for_task, for routes keyed by
    milestone_id."""

    def _check(
        request: Request, actor: Actor = Depends(get_current_actor), db: Session = Depends(get_db)
    ) -> Actor:
        milestone_id = UUID(request.path_params["milestone_id"])
        project_id = _resolve_project_id(db, milestone_id=milestone_id)
        if project_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found"
            )
        _assert_actor_can_access_project(actor, project_id, db)
        return actor

    return _check
