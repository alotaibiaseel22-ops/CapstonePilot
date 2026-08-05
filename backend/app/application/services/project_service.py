import logging
import uuid
from datetime import UTC, date, datetime

from app.application.ports.activity_event_repository import ActivityEventRepository
from app.application.ports.agent_run_repository import AgentRunRepository
from app.application.ports.invitation_repository import InvitationRepository
from app.application.ports.milestone_repository import MilestoneRepository
from app.application.ports.plan_repository import PlanRepository
from app.application.ports.project_member_repository import ProjectMemberRepository
from app.application.ports.project_repository import ProjectRepository
from app.application.ports.recommendation_repository import RecommendationRepository
from app.application.ports.risk_report_repository import RiskReportRepository
from app.application.ports.task_repository import TaskRepository
from app.domain.entities import Plan, Project
from app.domain.enums import PlanStatus, ProjectStatus

logger = logging.getLogger(__name__)


class ProjectNotFoundError(Exception):
    pass


class NotProjectOwnerError(Exception):
    pass


class ProjectService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        plan_repository: PlanRepository,
        project_member_repository: ProjectMemberRepository,
        invitation_repository: InvitationRepository,
        milestone_repository: MilestoneRepository,
        task_repository: TaskRepository,
        risk_report_repository: RiskReportRepository,
        recommendation_repository: RecommendationRepository,
        activity_event_repository: ActivityEventRepository,
        agent_run_repository: AgentRunRepository,
    ):
        self._projects = project_repository
        self._plans = plan_repository
        self._members = project_member_repository
        self._invitations = invitation_repository
        self._milestones = milestone_repository
        self._tasks = task_repository
        self._risk_reports = risk_report_repository
        self._recommendations = recommendation_repository
        self._activity_events = activity_event_repository
        self._agent_runs = agent_run_repository

    def create_project(
        self,
        name: str,
        description: str,
        owner_id: uuid.UUID,
        start_date: date | None = None,
        due_date: date | None = None,
    ) -> Project:
        now = datetime.now(UTC)
        project = Project(
            id=uuid.uuid4(),
            name=name,
            description=description,
            status=ProjectStatus.PLANNING,
            owner_id=owner_id,
            start_date=start_date,
            due_date=due_date,
            created_at=now,
        )
        created = self._projects.create(project)

        # Every project gets an initial draft Plan so Milestones/Tasks have
        # somewhere to attach per the architecture's Project -> Plan -> Milestone
        # chain. The Planner agent (Iteration 10+) will populate/version it.
        self._plans.create(
            Plan(
                id=uuid.uuid4(),
                project_id=created.id,
                version=1,
                status=PlanStatus.DRAFT,
                rationale={},
                created_at=now,
            )
        )
        return created

    def list_projects(self, user_id: uuid.UUID) -> list[Project]:
        """Only projects this user owns or is a member of - list_all() would
        leak every user's projects to every other authenticated user."""
        member_project_ids = {m.project_id for m in self._members.list_by_user(user_id)}
        return [
            project
            for project in self._projects.list_all()
            if project.owner_id == user_id or project.id in member_project_ids
        ]

    def get_project(self, project_id: uuid.UUID) -> Project:
        project = self._projects.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project {project_id} not found")
        return project

    def assert_owner(self, project_id: uuid.UUID, user_id: uuid.UUID) -> Project:
        """Verifies user_id owns this specific project - a global 'project_owner'
        role alone does not grant rights over every project, only the ones you own."""
        project = self.get_project(project_id)
        if project.owner_id != user_id:
            raise NotProjectOwnerError("Only this project's owner can do that")
        return project

    def update_project(
        self,
        project_id: uuid.UUID,
        requesting_user_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        status: ProjectStatus | None = None,
        start_date: date | None = None,
        due_date: date | None = None,
    ) -> Project:
        project = self.assert_owner(project_id, requesting_user_id)
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if status is not None:
            project.status = status
        if start_date is not None:
            project.start_date = start_date
        if due_date is not None:
            project.due_date = due_date
        return self._projects.update(project)

    def delete_project(self, project_id: uuid.UUID, requesting_user_id: uuid.UUID) -> None:
        """Deletes a project and everything hanging off it.

        Every project-child table's FK now also carries ondelete="CASCADE"
        (see the migration that added it, and the matching `ForeignKey(...,
        ondelete="CASCADE")` on each model) - enforced by Postgres always,
        and by SQLite too now that `session.py` turns on `PRAGMA
        foreign_keys` per connection. That makes this explicit walk a
        deliberate belt-and-braces duplicate of what the database would
        already do on its own, not the only thing standing between this and
        an IntegrityError: it stays because it's what actually caught this
        bug's root cause in the first place (a table - agent_runs - that
        was never added here even though its FK always pointed at
        projects.id), and because explicit deletion order/logging here is
        easier to reason about and debug than an opaque cascade. If a table
        is ever added that should survive project deletion (e.g. an audit
        record kept for compliance), delete everything else here first,
        leave that one out, and give its FK ondelete="SET NULL" instead of
        CASCADE in its migration - don't just rely on forgetting to add it
        here, since the DB-level CASCADE would delete it anyway."""
        self.assert_owner(project_id, requesting_user_id)

        try:
            task_count = 0
            milestone_count = 0
            plan_count = 0
            for plan in self._plans.list_by_project(project_id):
                for milestone in self._milestones.list_by_plan(plan.id):
                    for task in self._tasks.list_by_milestone(milestone.id):
                        self._tasks.delete(task.id)
                        task_count += 1
                    self._milestones.delete(milestone.id)
                    milestone_count += 1
                self._plans.delete(plan.id)
                plan_count += 1

            self._recommendations.delete_by_project(project_id)
            self._risk_reports.delete_by_project(project_id)
            self._agent_runs.delete_by_project(project_id)
            self._activity_events.delete_by_project(project_id)
            self._members.delete_by_project(project_id)
            self._invitations.delete_by_project(project_id)
            self._projects.delete(project_id)
        except Exception:
            logger.exception(
                "Failed to delete project %s (requested by user %s) - "
                "%d plan(s)/%d milestone(s)/%d task(s) were removed before the failure. "
                "If this is an IntegrityError, a child table referencing projects.id "
                "(directly or transitively) is missing ondelete=CASCADE on its FK, or "
                "is missing from this method's explicit cascade above - check "
                "app/infrastructure/db/models/ for every ForeignKey(\"projects.id\", ...) "
                "and confirm this project_id has no remaining rows in that table.",
                project_id,
                requesting_user_id,
                plan_count,
                milestone_count,
                task_count,
            )
            raise

        logger.info("Deleted project %s (requested by user %s)", project_id, requesting_user_id)
