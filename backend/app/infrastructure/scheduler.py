import asyncio
import logging
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.decision_engine.rules import compute_signals
from app.application.ports.risk_orchestrator import RiskAnalysisOrchestratorPort
from app.application.services.activity_service import ActivityService
from app.domain.entities import AgentRun, Project, Recommendation, RiskReport
from app.domain.enums import AgentRunStatus, ProjectStatus, RecommendationStatus, RiskSeverity
from app.infrastructure.agents.error_classification import describe_error
from app.infrastructure.agents.risk_cache import get_cached_analysis, set_cached_analysis
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
from app.infrastructure.db.repositories.recommendation_repository import (
    SqlAlchemyRecommendationRepository,
)
from app.infrastructure.db.repositories.risk_report_repository import SqlAlchemyRiskReportRepository
from app.infrastructure.db.repositories.task_repository import SqlAlchemyTaskRepository
from app.infrastructure.db.repositories.user_repository import SqlAlchemyUserRepository

logger = logging.getLogger(__name__)

# A completed project is finished; an archived one is deliberately set aside
# by its owner - neither should keep spending free-tier signal checks (or,
# on a breach, a paid Gemini call) every 30 minutes.
_MONITORING_EXEMPT_STATUSES = (ProjectStatus.COMPLETED, ProjectStatus.ARCHIVED)


def _check_project(
    db: Session, project: Project, risk_orchestrator: RiskAnalysisOrchestratorPort
) -> bool:
    """The free-signals -> breach check -> cache check -> one Gemini call ->
    persist pipeline for exactly one project, on the given (already-open)
    session. Shared by the periodic tick (run_monitoring_tick, looping every
    non-completed project) and every event-triggered immediate check
    (run_immediate_risk_check, one project) - "should this project be
    analyzed right now" only has one implementation.

    Returns True if this call hit a QUOTA_EXCEEDED failure, so a caller
    looping over multiple projects (the tick) knows to stop early instead of
    hammering an already-exhausted quota project by project."""
    # No owner-defined deadline means no schedule-based analysis - never
    # guess a deadline, and never let the LLM reason about days-remaining/
    # schedule-compression risks that don't have a real deadline behind them.
    if project.due_date is None:
        return False

    plans_repo = SqlAlchemyPlanRepository(db)
    milestones_repo = SqlAlchemyMilestoneRepository(db)
    tasks_repo = SqlAlchemyTaskRepository(db)
    risk_reports_repo = SqlAlchemyRiskReportRepository(db)
    recommendations_repo = SqlAlchemyRecommendationRepository(db)
    agent_runs_repo = SqlAlchemyAgentRunRepository(db)
    activity_repo = SqlAlchemyActivityEventRepository(db)

    milestones = [
        milestone
        for plan in plans_repo.list_by_project(project.id)
        for milestone in milestones_repo.list_by_plan(plan.id)
    ]
    tasks = [
        task for milestone in milestones for task in tasks_repo.list_by_milestone(milestone.id)
    ]
    signals = compute_signals(project, tasks, milestones)
    if not signals.breached:
        return False

    # A cache hit means this exact signal state was already analyzed and
    # recorded (on a previous tick, or a previous immediate check) - skip
    # both the Gemini call AND re-persisting the same findings as duplicate
    # rows. Checked here (not inside the orchestrator) since this is the
    # only caller of analyze(), and every implementation of the port - fake
    # or real - should skip re-recording an unchanged breach the same way.
    cached_output = get_cached_analysis(signals)
    if cached_output is not None:
        return False

    now = datetime.now(UTC)
    agent_run = agent_runs_repo.create(
        AgentRun(
            id=uuid.uuid4(),
            project_id=project.id,
            agent_type="risk_analysis",
            status=AgentRunStatus.RUNNING,
            input_ref={"breach_reasons": signals.breach_reasons},
            output_ref=None,
            error=None,
            created_at=now,
            updated_at=now,
        )
    )

    current_plan = plans_repo.get_current_for_project(project.id)
    task_summary = "; ".join(t.title for t in tasks[:20])
    dependencies = (current_plan.rationale.get("dependencies") if current_plan else None) or []
    dependencies_text = "; ".join(dependencies)
    recent_activity = activity_repo.list_by_project(project.id, limit=10)
    activity_text = "; ".join(event.message for event in recent_activity)

    try:
        output = risk_orchestrator.analyze(
            project.name,
            project.description,
            signals,
            task_summary,
            dependencies_text,
            activity_text,
        )

        risk_ids: list[uuid.UUID] = []
        for risk_item in output.risks:
            created_risk = risk_reports_repo.create(
                RiskReport(
                    id=uuid.uuid4(),
                    project_id=project.id,
                    plan_version=current_plan.version if current_plan else 1,
                    severity=RiskSeverity(risk_item.severity),
                    category=risk_item.category,
                    title=risk_item.title,
                    description=risk_item.description,
                    created_at=datetime.now(UTC),
                )
            )
            risk_ids.append(created_risk.id)

        for rec_item in output.recommendations:
            risk_report_id = (
                risk_ids[rec_item.risk_index]
                if rec_item.risk_index is not None and rec_item.risk_index < len(risk_ids)
                else None
            )
            recommendations_repo.create(
                Recommendation(
                    id=uuid.uuid4(),
                    risk_report_id=risk_report_id,
                    project_id=project.id,
                    title=rec_item.title,
                    category=rec_item.category,
                    severity=rec_item.severity,
                    effort=rec_item.effort,
                    impact=rec_item.impact,
                    description=rec_item.description,
                    rationale=rec_item.rationale or None,
                    proposed_changes={},
                    status=RecommendationStatus.PENDING,
                    created_at=datetime.now(UTC),
                )
            )

        agent_runs_repo.update_status(
            agent_run.id,
            AgentRunStatus.SUCCEEDED,
            output_ref={
                "risk_count": len(output.risks),
                "recommendation_count": len(output.recommendations),
            },
        )
        set_cached_analysis(signals, output)

        if output.risks:
            ActivityService(
                SqlAlchemyActivityEventRepository(db),
                SqlAlchemyProjectRepository(db),
                SqlAlchemyProjectMemberRepository(db),
                SqlAlchemyUserRepository(db),
            ).log_risk_detected(project.id, len(output.risks))

        return False
    except Exception as exc:  # noqa: BLE001 - background job/tick boundary
        description = describe_error(exc)
        try:
            agent_runs_repo.update_status(agent_run.id, AgentRunStatus.FAILED, error=description)
        except Exception:  # noqa: BLE001 - e.g. the agent_run row itself is unreachable
            pass
        return description.startswith("QUOTA_EXCEEDED")


def run_monitoring_tick(
    session_factory: Callable[[], Session],
    risk_orchestrator: RiskAnalysisOrchestratorPort,
) -> None:
    """One scheduler tick: _check_project runs for every non-completed
    project. Standalone and directly callable - not buried in the asyncio
    loop below - so tests and manual verification can run exactly one tick
    without waiting the real 30-minute interval. Opens its own DB session
    since it runs outside any request, same reasoning as
    orchestrator_service.run_planning_job."""
    db = session_factory()
    try:
        projects_repo = SqlAlchemyProjectRepository(db)
        for project in projects_repo.list_all():
            if project.status in _MONITORING_EXEMPT_STATUSES:
                continue
            if _check_project(db, project, risk_orchestrator):
                # Don't hammer an already-exhausted quota project by project -
                # the next tick (30 min later) tries again.
                logger.warning("Monitoring tick stopped early: Gemini quota exceeded")
                return
    finally:
        db.close()


def _resolve_project_id(
    db: Session, *, task_id: UUID | None = None, milestone_id: UUID | None = None
) -> UUID | None:
    """Walks task -> milestone -> plan -> project (or milestone -> plan ->
    project) to find which project an immediate check is for. Needed because
    the task/milestone update endpoints don't have project_id in their URL."""
    if milestone_id is None and task_id is not None:
        task = SqlAlchemyTaskRepository(db).get_by_id(task_id)
        if task is None:
            return None
        milestone_id = task.milestone_id

    if milestone_id is not None:
        milestone = SqlAlchemyMilestoneRepository(db).get_by_id(milestone_id)
        if milestone is None:
            return None
        plan = SqlAlchemyPlanRepository(db).get_by_id(milestone.plan_id)
        return plan.project_id if plan else None

    return None


def run_immediate_risk_check(
    session_factory: Callable[[], Session],
    risk_orchestrator: RiskAnalysisOrchestratorPort,
    *,
    project_id: UUID | None = None,
    task_id: UUID | None = None,
    milestone_id: UUID | None = None,
) -> None:
    """Scheduled as a FastAPI BackgroundTask right after a project-affecting
    event (project created/updated, a task or milestone updated, a plan
    generated) so users see updated risks without waiting for the next
    30-minute tick. Runs outside the request (opens its own session, same as
    run_monitoring_tick) and fires unconditionally - compute_signals is free
    and the cache already gates the one thing that costs money (the Gemini
    call), so there's no need to filter by which field actually changed."""
    db = session_factory()
    try:
        if project_id is None:
            project_id = _resolve_project_id(db, task_id=task_id, milestone_id=milestone_id)
        if project_id is None:
            return

        project = SqlAlchemyProjectRepository(db).get_by_id(project_id)
        if project is None or project.status in _MONITORING_EXEMPT_STATUSES:
            return

        _check_project(db, project, risk_orchestrator)
    finally:
        db.close()


async def run_monitoring_loop(
    session_factory: Callable[[], Session],
    risk_orchestrator: RiskAnalysisOrchestratorPort,
    interval_seconds: int,
) -> None:
    """Started as a plain asyncio background task from main.py's lifespan -
    no new deployed infra, matching the architecture's existing
    "BackgroundTasks over Celery" trade-off."""
    while True:
        try:
            await asyncio.to_thread(run_monitoring_tick, session_factory, risk_orchestrator)
        except Exception:  # noqa: BLE001 - the loop itself must never die
            logger.exception("Monitoring tick failed")
        await asyncio.sleep(interval_seconds)
