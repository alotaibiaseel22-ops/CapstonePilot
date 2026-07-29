import logging
import uuid
from collections.abc import Callable
from datetime import timedelta

from sqlalchemy.orm import Session

from app.application.ports.planning_orchestrator import PlanningOrchestratorPort
from app.application.ports.risk_orchestrator import RiskAnalysisOrchestratorPort
from app.application.services.activity_service import ActivityService
from app.application.services.milestone_service import MilestoneService
from app.application.services.plan_service import PlanService
from app.application.services.task_service import TaskService
from app.domain.enums import AgentRunStatus, TaskPriority
from app.infrastructure.agents.error_classification import describe_error
from app.infrastructure.db.repositories.activity_event_repository import (
    SqlAlchemyActivityEventRepository,
)
from app.infrastructure.db.repositories.agent_run_repository import SqlAlchemyAgentRunRepository
from app.infrastructure.db.repositories.milestone_repository import SqlAlchemyMilestoneRepository
from app.infrastructure.db.repositories.plan_repository import SqlAlchemyPlanRepository
from app.infrastructure.db.repositories.project_member_repository import (
    SqlAlchemyProjectMemberRepository,
)
from app.infrastructure.db.repositories.project_repository import SqlAlchemyProjectRepository
from app.infrastructure.db.repositories.task_repository import SqlAlchemyTaskRepository
from app.infrastructure.db.repositories.user_repository import SqlAlchemyUserRepository
from app.infrastructure.scheduler import _check_project

logger = logging.getLogger(__name__)


def run_planning_job(
    agent_run_id: uuid.UUID,
    project_id: uuid.UUID,
    project_name: str,
    project_description: str,
    proposal_text: str,
    session_factory: Callable[[], Session],
    orchestrator: PlanningOrchestratorPort,
    risk_orchestrator: RiskAnalysisOrchestratorPort,
) -> None:
    """Runs OUTSIDE any request - scheduled via BackgroundTasks, so it opens its
    own DB session rather than reusing the (already-closed-by-then) request
    session, and is a plain sync function so Starlette runs it in a threadpool
    instead of blocking the event loop on the crew's network calls.

    Deliberately swallows and records any failure (bad LLM output, network
    error, whatever) as AgentRun.failed rather than raising - there is no
    caller left to catch it by the time this runs in the background.

    On success, also runs an immediate risk check on the same already-open
    session - a freshly-generated plan is exactly the kind of "project
    material upload" / "AI plan generation" event that should surface risks
    right away rather than waiting for the next 30-minute scheduler tick."""
    db = session_factory()
    try:
        agent_runs = SqlAlchemyAgentRunRepository(db)
        projects = SqlAlchemyProjectRepository(db)
        plans = SqlAlchemyPlanRepository(db)
        milestones_repo = SqlAlchemyMilestoneRepository(db)
        tasks_repo = SqlAlchemyTaskRepository(db)

        milestone_service = MilestoneService(milestones_repo, plans)
        task_service = TaskService(tasks_repo)
        plan_service = PlanService(plans, projects, milestones_repo, tasks_repo)
        activity_service = ActivityService(
            SqlAlchemyActivityEventRepository(db),
            projects,
            SqlAlchemyProjectMemberRepository(db),
            SqlAlchemyUserRepository(db),
        )

        try:
            agent_runs.update_status(agent_run_id, AgentRunStatus.RUNNING)

            output = orchestrator.generate_plan(project_name, project_description, proposal_text)

            project = projects.get_by_id(project_id)
            base_date = (project.start_date if project else None) or (
                project.created_at.date() if project else None
            )
            plan = plan_service.get_current_plan(project_id)
            total_task_count = 0

            for order, milestone_plan in enumerate(output.milestones):
                milestone = milestone_service.create_milestone(
                    project_id,
                    milestone_plan.title,
                    base_date + timedelta(days=milestone_plan.days_from_start)
                    if base_date
                    else None,
                    order=order,
                )
                for task_plan in milestone_plan.tasks:
                    task_service.create_task(
                        milestone.id,
                        task_plan.title,
                        description=task_plan.description,
                        priority=TaskPriority(task_plan.priority),
                        due_date=base_date + timedelta(days=task_plan.days_from_start)
                        if base_date
                        else None,
                    )
                    total_task_count += 1

            plan_service.mark_proposed(
                plan.id,
                {
                    "summary": output.summary,
                    "dependencies": output.dependencies,
                    "estimated_timeline": output.estimated_timeline,
                },
            )
            agent_runs.update_status(
                agent_run_id,
                AgentRunStatus.SUCCEEDED,
                output_ref={"summary": output.summary, "milestone_count": len(output.milestones)},
            )
            activity_service.log_plan_generated(
                project_id, len(output.milestones), total_task_count
            )

            if project is not None:
                try:
                    _check_project(db, project, risk_orchestrator)
                except Exception:  # noqa: BLE001 - never let a risk-check failure
                    # mask the Planner's own success above; the next scheduled
                    # tick will simply retry this project like any other.
                    logger.exception(
                        "Immediate risk check after plan generation failed for project %s",
                        project_id,
                    )
        except Exception as exc:  # noqa: BLE001 - background job boundary, see docstring
            try:
                agent_runs.update_status(
                    agent_run_id, AgentRunStatus.FAILED, error=describe_error(exc)
                )
            except Exception:  # noqa: BLE001 - e.g. the agent_run row itself is unreachable
                pass
    finally:
        db.close()
