from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from statistics import pstdev
from uuid import UUID

from app.domain.entities import Milestone, Project, Task
from app.domain.enums import TaskStatus

# Per architecture.md section 6 - crossing any one of these marks a project as
# "breached" and worth spending a paid Gemini call on. Kept as module
# constants (not config) since tuning them is a code change, not an ops one.
SCHEDULE_VARIANCE_THRESHOLD = 0.15
OVERDUE_RATIO_THRESHOLD = 0.2
WORKLOAD_IMBALANCE_THRESHOLD = 2.0
INACTIVITY_DAYS_THRESHOLD = 7


@dataclass
class ProjectSignals:
    project_id: UUID
    schedule_variance: float
    overdue_ratio: float
    workload_imbalance: float
    total_tasks: int
    overdue_tasks: int
    days_since_last_activity: int | None
    breached: bool
    # Owner-defined-deadline-aware fields (see docs/architecture.md) - all
    # derived here, never guessed by the LLM. days_remaining/progress_percent
    # are None/0.0 when there's nothing to compute them from (no due_date,
    # no tasks) rather than a misleading number.
    days_remaining: int | None = None
    progress_percent: float = 0.0
    completed_tasks: int = 0
    pending_tasks: int = 0
    completed_milestones: int = 0
    pending_milestones: int = 0
    overdue_milestones: int = 0
    breach_reasons: list[str] = field(default_factory=list)


def compute_signals(
    project: Project,
    tasks: list[Task],
    milestones: list[Milestone] | None = None,
    as_of: date | None = None,
) -> ProjectSignals:
    """Pure, local, zero-cost - runs on every scheduler tick for every
    non-completed project so the paid Gemini call only ever fires for a
    project that actually crosses a threshold (the LLM interprets facts, it
    never computes them)."""
    today = as_of or datetime.now(UTC).date()
    milestones = milestones or []
    total_tasks = len(tasks)
    days_remaining = (project.due_date - today).days if project.due_date else None

    if total_tasks == 0:
        # An empty project is new, not stale - inactivity only applies once
        # there's actually been some activity to go quiet on.
        return ProjectSignals(
            project_id=project.id,
            schedule_variance=0.0,
            overdue_ratio=0.0,
            workload_imbalance=0.0,
            total_tasks=0,
            overdue_tasks=0,
            days_since_last_activity=None,
            breached=False,
            days_remaining=days_remaining,
            pending_milestones=len(milestones),
        )

    overdue_tasks = sum(
        1
        for t in tasks
        if t.status != TaskStatus.DONE and t.due_date is not None and t.due_date < today
    )
    overdue_ratio = overdue_tasks / total_tasks
    completed_tasks = sum(1 for t in tasks if t.status == TaskStatus.DONE)
    done_fraction = completed_tasks / total_tasks
    progress_percent = done_fraction * 100

    # Milestone completion/overdue is derived, not stored - a Milestone has
    # no status column, so "complete" means every one of its tasks is done,
    # and "overdue" means its own due_date has passed while it isn't.
    tasks_by_milestone: dict[UUID, list[Task]] = {}
    for t in tasks:
        tasks_by_milestone.setdefault(t.milestone_id, []).append(t)
    completed_milestones = 0
    pending_milestones = 0
    overdue_milestones = 0
    for m in milestones:
        m_tasks = tasks_by_milestone.get(m.id, [])
        is_complete = bool(m_tasks) and all(t.status == TaskStatus.DONE for t in m_tasks)
        if is_complete:
            completed_milestones += 1
        else:
            pending_milestones += 1
            if m.due_date is not None and m.due_date < today:
                overdue_milestones += 1

    # No start_date recorded yet falls back to created_at, same convention
    # orchestrator_service.py already uses for the Planner's base_date.
    start_date = project.start_date or project.created_at.date()
    schedule_variance = 0.0
    if project.due_date and project.due_date > start_date:
        elapsed_fraction = min(
            max((today - start_date).days / (project.due_date - start_date).days, 0.0), 1.0
        )
        schedule_variance = elapsed_fraction - done_fraction

    open_counts_by_assignee: dict[UUID, int] = {}
    for t in tasks:
        if t.assignee_id is not None and t.status != TaskStatus.DONE:
            open_counts_by_assignee[t.assignee_id] = (
                open_counts_by_assignee.get(t.assignee_id, 0) + 1
            )
    # Population stddev needs >=2 assignees to mean anything - a single
    # assignee (or none) is never "imbalanced" relative to a team.
    workload_imbalance = (
        pstdev(open_counts_by_assignee.values()) if len(open_counts_by_assignee) > 1 else 0.0
    )

    # "Missed deadlines" is overdue_ratio above, not a separate signal.
    # Inactivity is its own thing: a project can be on-schedule on paper and
    # still have gone quiet - no task has been touched in days.
    last_activity = max(t.updated_at for t in tasks).date()
    days_since_last_activity = (today - last_activity).days

    breach_reasons = []
    if schedule_variance > SCHEDULE_VARIANCE_THRESHOLD:
        breach_reasons.append(f"Schedule variance {schedule_variance:.0%} exceeds threshold")
    if overdue_ratio > OVERDUE_RATIO_THRESHOLD:
        breach_reasons.append(f"{overdue_tasks}/{total_tasks} tasks overdue ({overdue_ratio:.0%})")
    if workload_imbalance > WORKLOAD_IMBALANCE_THRESHOLD:
        breach_reasons.append(
            f"Workload imbalance (stddev {workload_imbalance:.1f} open tasks/assignee)"
        )
    if days_since_last_activity > INACTIVITY_DAYS_THRESHOLD:
        breach_reasons.append(f"No task activity in {days_since_last_activity} days")
    if overdue_milestones > 0:
        breach_reasons.append(f"{overdue_milestones} milestone(s) overdue")

    return ProjectSignals(
        project_id=project.id,
        schedule_variance=schedule_variance,
        overdue_ratio=overdue_ratio,
        workload_imbalance=workload_imbalance,
        total_tasks=total_tasks,
        overdue_tasks=overdue_tasks,
        days_since_last_activity=days_since_last_activity,
        breached=bool(breach_reasons),
        days_remaining=days_remaining,
        progress_percent=progress_percent,
        completed_tasks=completed_tasks,
        pending_tasks=total_tasks - completed_tasks,
        completed_milestones=completed_milestones,
        pending_milestones=pending_milestones,
        overdue_milestones=overdue_milestones,
        breach_reasons=breach_reasons,
    )
