import uuid
from datetime import UTC, datetime
from uuid import UUID

from app.application.ports.activity_event_repository import ActivityEventRepository
from app.application.ports.project_member_repository import ProjectMemberRepository
from app.application.ports.project_repository import ProjectRepository
from app.application.ports.user_repository import UserRepository
from app.domain.entities import ActivityEvent, Project, User


class ActivityService:
    """One log() call per meaningful, non-noisy project event (see
    architecture.md's event-scope list) - deliberately not threaded through
    every other service's constructor. Call sites live in the routers/
    background jobs right after their existing action succeeds, the same
    shape Iteration 12b already established for the immediate risk-check
    trigger."""

    def __init__(
        self,
        activity_event_repository: ActivityEventRepository,
        project_repository: ProjectRepository,
        project_member_repository: ProjectMemberRepository,
        user_repository: UserRepository,
    ):
        self._events = activity_event_repository
        self._projects = project_repository
        self._members = project_member_repository
        self._users = user_repository

    def _log(
        self, project_id: UUID, actor_id: UUID | None, event_type: str, message: str
    ) -> ActivityEvent:
        return self._events.create(
            ActivityEvent(
                id=uuid.uuid4(),
                project_id=project_id,
                actor_id=actor_id,
                event_type=event_type,
                message=message,
                created_at=datetime.now(UTC),
            )
        )

    def log_project_created(self, project: Project, actor: User) -> ActivityEvent:
        return self._log(
            project.id, actor.id, "project_created", f"{actor.name} created the project"
        )

    def log_plan_generated(
        self, project_id: UUID, milestone_count: int, task_count: int
    ) -> ActivityEvent:
        return self._log(
            project_id,
            None,
            "plan_generated",
            f"AI generated an initial plan with {milestone_count} milestones "
            f"and {task_count} tasks",
        )

    def log_plan_approved(self, project_id: UUID, actor: User) -> ActivityEvent:
        return self._log(
            project_id, actor.id, "plan_approved", f"{actor.name} approved the project plan"
        )

    def log_plan_rejected(self, project_id: UUID, actor: User) -> ActivityEvent:
        return self._log(
            project_id, actor.id, "plan_rejected", f"{actor.name} rejected the project plan"
        )

    def log_task_completed(self, project_id: UUID, actor: User, task_title: str) -> ActivityEvent:
        return self._log(
            project_id, actor.id, "task_completed", f'{actor.name} completed "{task_title}"'
        )

    def log_risk_detected(self, project_id: UUID, risk_count: int) -> ActivityEvent:
        label = "risk" if risk_count == 1 else "risks"
        return self._log(project_id, None, "risk_detected", f"AI detected {risk_count} new {label}")

    def log_recommendation_approved(
        self, project_id: UUID, actor: User, title: str
    ) -> ActivityEvent:
        return self._log(
            project_id,
            actor.id,
            "recommendation_approved",
            f'{actor.name} accepted the recommendation "{title}"',
        )

    def log_recommendation_rejected(
        self, project_id: UUID, actor: User, title: str
    ) -> ActivityEvent:
        return self._log(
            project_id,
            actor.id,
            "recommendation_rejected",
            f'{actor.name} dismissed the recommendation "{title}"',
        )

    def log_member_joined(self, project_id: UUID, actor: User) -> ActivityEvent:
        return self._log(project_id, actor.id, "member_joined", f"{actor.name} joined the project")

    def list_project_activity(self, project_id: UUID) -> list[ActivityEvent]:
        return self._events.list_by_project(project_id)

    def _project_ids_for_user(self, user_id: UUID) -> list[UUID]:
        # Same owner-or-member lookup ProjectService.list_projects uses -
        # duplicated rather than depending on ProjectService directly, since
        # no service in this codebase depends on another service, only on
        # ports/repositories.
        member_project_ids = {m.project_id for m in self._members.list_by_user(user_id)}
        return [
            p.id
            for p in self._projects.list_all()
            if p.owner_id == user_id or p.id in member_project_ids
        ]

    def get_unread_count(self, user: User) -> int:
        project_ids = self._project_ids_for_user(user.id)
        return self._events.count_since(project_ids, user.notifications_last_seen_at)

    def mark_seen(self, user: User) -> User:
        user.notifications_last_seen_at = datetime.now(UTC)
        return self._users.update(user)
