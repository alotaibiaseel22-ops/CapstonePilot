import uuid
from datetime import UTC, date, datetime, timedelta

from app.application.decision_engine.rules import (
    INACTIVITY_DAYS_THRESHOLD,
    OVERDUE_RATIO_THRESHOLD,
    SCHEDULE_VARIANCE_THRESHOLD,
    WORKLOAD_IMBALANCE_THRESHOLD,
    compute_signals,
)
from app.domain.entities import Milestone, Project, Task
from app.domain.enums import ProjectStatus, TaskPriority, TaskStatus

TODAY = date(2026, 7, 19)


def make_project(**overrides) -> Project:
    defaults = dict(
        id=uuid.uuid4(),
        name="Test Project",
        description="desc",
        status=ProjectStatus.ACTIVE,
        owner_id=uuid.uuid4(),
        start_date=date(2026, 6, 1),
        due_date=date(2026, 8, 1),
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    defaults.update(overrides)
    return Project(**defaults)


def make_milestone(**overrides) -> Milestone:
    defaults = dict(
        id=uuid.uuid4(),
        plan_id=uuid.uuid4(),
        title="Milestone",
        due_date=None,
        order=0,
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    defaults.update(overrides)
    return Milestone(**defaults)


def make_task(**overrides) -> Task:
    defaults = dict(
        id=uuid.uuid4(),
        milestone_id=uuid.uuid4(),
        title="Task",
        description="",
        status=TaskStatus.PENDING,
        priority=TaskPriority.MEDIUM,
        assignee_id=None,
        due_date=None,
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
        # Recent by default (one day before TODAY) so existing tests don't
        # accidentally trip the inactivity signal - tests exercising it
        # override this explicitly with an old timestamp.
        updated_at=datetime(2026, 7, 18, tzinfo=UTC),
    )
    defaults.update(overrides)
    return Task(**defaults)


def test_zero_tasks_is_never_breached():
    project = make_project()
    signals = compute_signals(project, [], as_of=TODAY)
    assert signals.total_tasks == 0
    assert signals.overdue_tasks == 0
    assert signals.schedule_variance == 0.0
    assert signals.workload_imbalance == 0.0
    assert signals.breached is False
    assert signals.breach_reasons == []
    assert signals.days_since_last_activity is None


def test_no_start_date_falls_back_to_created_at():
    project = make_project(
        start_date=None, due_date=date(2026, 8, 1), created_at=datetime(2026, 6, 1, tzinfo=UTC)
    )
    tasks = [make_task(status=TaskStatus.DONE) for _ in range(4)]
    signals = compute_signals(project, tasks, as_of=TODAY)
    # Fully done, so however elapsed_fraction lands, schedule_variance stays <= 0.
    assert signals.schedule_variance <= 0.0


def test_high_overdue_ratio_breaches():
    tasks = [
        make_task(status=TaskStatus.PENDING, due_date=TODAY - timedelta(days=5)) for _ in range(3)
    ] + [make_task(status=TaskStatus.DONE, due_date=TODAY - timedelta(days=5))]
    project = make_project()
    signals = compute_signals(project, tasks, as_of=TODAY)

    assert signals.overdue_tasks == 3
    assert signals.overdue_ratio == 3 / 4
    assert signals.overdue_ratio > OVERDUE_RATIO_THRESHOLD
    assert signals.breached is True
    assert any("overdue" in reason for reason in signals.breach_reasons)


def test_done_tasks_are_never_counted_as_overdue():
    tasks = [
        make_task(status=TaskStatus.DONE, due_date=TODAY - timedelta(days=30)) for _ in range(5)
    ]
    project = make_project()
    signals = compute_signals(project, tasks, as_of=TODAY)
    assert signals.overdue_tasks == 0
    assert signals.overdue_ratio == 0.0


def test_schedule_variance_breaches_when_far_behind():
    # Project is 90% elapsed but nothing is done yet.
    project = make_project(start_date=date(2026, 6, 1), due_date=date(2026, 6, 11))
    tasks = [make_task(status=TaskStatus.PENDING) for _ in range(4)]
    signals = compute_signals(project, tasks, as_of=date(2026, 6, 10))

    assert signals.schedule_variance > SCHEDULE_VARIANCE_THRESHOLD
    assert signals.breached is True
    assert any("Schedule variance" in reason for reason in signals.breach_reasons)


def test_workload_imbalance_breaches_with_lopsided_assignment():
    heavy = uuid.uuid4()
    light = uuid.uuid4()
    tasks = [make_task(status=TaskStatus.PENDING, assignee_id=heavy) for _ in range(8)] + [
        make_task(status=TaskStatus.PENDING, assignee_id=light)
    ]
    project = make_project()
    signals = compute_signals(project, tasks, as_of=TODAY)

    assert signals.workload_imbalance > WORKLOAD_IMBALANCE_THRESHOLD
    assert signals.breached is True
    assert any("Workload imbalance" in reason for reason in signals.breach_reasons)


def test_single_assignee_is_never_imbalanced():
    solo = uuid.uuid4()
    tasks = [make_task(status=TaskStatus.PENDING, assignee_id=solo) for _ in range(6)]
    project = make_project()
    signals = compute_signals(project, tasks, as_of=TODAY)
    assert signals.workload_imbalance == 0.0


def test_healthy_project_is_not_breached():
    project = make_project(start_date=date(2026, 6, 1), due_date=date(2026, 12, 1))
    tasks = [
        make_task(status=TaskStatus.DONE, due_date=date(2026, 6, 15)),
        make_task(status=TaskStatus.IN_PROGRESS, due_date=date(2026, 7, 25)),
        make_task(status=TaskStatus.PENDING, due_date=date(2026, 8, 1)),
    ]
    signals = compute_signals(project, tasks, as_of=TODAY)
    assert signals.breached is False
    assert signals.breach_reasons == []


def test_stale_project_breaches_due_to_inactivity():
    # Otherwise healthy - on schedule (done_fraction tracks elapsed_fraction),
    # nothing overdue, no assignees to imbalance - the only thing wrong is
    # that nobody has touched a task in weeks.
    project = make_project(start_date=date(2026, 6, 1), due_date=date(2026, 8, 1))
    stale_update = datetime(2026, 6, 20, tzinfo=UTC)
    tasks = [make_task(status=TaskStatus.DONE, updated_at=stale_update) for _ in range(4)] + [
        make_task(status=TaskStatus.PENDING, due_date=date(2026, 8, 1), updated_at=stale_update)
    ]
    signals = compute_signals(project, tasks, as_of=TODAY)

    expected_days = (TODAY - stale_update.date()).days
    assert expected_days > INACTIVITY_DAYS_THRESHOLD
    assert signals.days_since_last_activity == expected_days
    assert (
        abs(signals.schedule_variance) < SCHEDULE_VARIANCE_THRESHOLD
    )  # not breaching for this reason
    assert signals.overdue_ratio == 0.0
    assert signals.breached is True
    assert any("No task activity" in reason for reason in signals.breach_reasons)


def test_recently_updated_project_is_not_inactive():
    # Project just started (elapsed_fraction ~0), so schedule_variance
    # doesn't confound the inactivity-specific assertion below.
    project = make_project(start_date=date(2026, 7, 18), due_date=date(2026, 12, 1))
    tasks = [
        make_task(
            status=TaskStatus.PENDING,
            due_date=date(2026, 8, 1),
            updated_at=datetime(2026, 7, 17, tzinfo=UTC),
        ),
        make_task(
            status=TaskStatus.PENDING,
            due_date=date(2026, 9, 1),
            updated_at=datetime(2026, 7, 19, tzinfo=UTC),
        ),
    ]
    signals = compute_signals(project, tasks, as_of=TODAY)

    assert signals.days_since_last_activity == 0
    assert signals.breached is False
    assert not any("No task activity" in reason for reason in signals.breach_reasons)


def test_inactivity_uses_the_most_recently_updated_task():
    project = make_project(start_date=date(2026, 6, 1), due_date=date(2026, 12, 1))
    tasks = [
        make_task(updated_at=datetime(2026, 6, 1, tzinfo=UTC)),
        make_task(updated_at=datetime(2026, 7, 15, tzinfo=UTC)),  # most recent
        make_task(updated_at=datetime(2026, 6, 20, tzinfo=UTC)),
    ]
    signals = compute_signals(project, tasks, as_of=TODAY)
    assert signals.days_since_last_activity == (TODAY - date(2026, 7, 15)).days


def test_days_remaining_is_none_without_a_deadline():
    project = make_project(due_date=None)
    signals = compute_signals(project, [make_task()], as_of=TODAY)
    assert signals.days_remaining is None


def test_days_remaining_counts_down_to_the_deadline():
    project = make_project(due_date=TODAY + timedelta(days=10))
    signals = compute_signals(project, [make_task()], as_of=TODAY)
    assert signals.days_remaining == 10


def test_progress_percent_and_task_counts():
    tasks = [make_task(status=TaskStatus.DONE) for _ in range(3)] + [
        make_task(status=TaskStatus.PENDING) for _ in range(1)
    ]
    project = make_project()
    signals = compute_signals(project, tasks, as_of=TODAY)
    assert signals.completed_tasks == 3
    assert signals.pending_tasks == 1
    assert signals.progress_percent == 75.0


def test_milestone_is_complete_only_when_every_task_is_done():
    milestone = make_milestone()
    tasks = [
        make_task(milestone_id=milestone.id, status=TaskStatus.DONE),
        make_task(milestone_id=milestone.id, status=TaskStatus.IN_PROGRESS),
    ]
    project = make_project()
    signals = compute_signals(project, tasks, [milestone], as_of=TODAY)
    assert signals.completed_milestones == 0
    assert signals.pending_milestones == 1


def test_milestone_with_all_tasks_done_counts_as_completed():
    milestone = make_milestone()
    tasks = [make_task(milestone_id=milestone.id, status=TaskStatus.DONE) for _ in range(2)]
    project = make_project()
    signals = compute_signals(project, tasks, [milestone], as_of=TODAY)
    assert signals.completed_milestones == 1
    assert signals.pending_milestones == 0
    assert signals.overdue_milestones == 0


def test_overdue_milestone_is_detected_and_breaches():
    milestone = make_milestone(due_date=TODAY - timedelta(days=3))
    tasks = [make_task(milestone_id=milestone.id, status=TaskStatus.IN_PROGRESS)]
    project = make_project()
    signals = compute_signals(project, tasks, [milestone], as_of=TODAY)
    assert signals.overdue_milestones == 1
    assert signals.breached is True
    assert any("milestone" in reason for reason in signals.breach_reasons)


def test_a_past_due_but_completed_milestone_is_not_overdue():
    milestone = make_milestone(due_date=TODAY - timedelta(days=3))
    tasks = [make_task(milestone_id=milestone.id, status=TaskStatus.DONE)]
    project = make_project()
    signals = compute_signals(project, tasks, [milestone], as_of=TODAY)
    assert signals.completed_milestones == 1
    assert signals.overdue_milestones == 0


def test_empty_project_still_reports_milestone_and_deadline_context():
    project = make_project(due_date=TODAY + timedelta(days=5))
    signals = compute_signals(project, [], [make_milestone(), make_milestone()], as_of=TODAY)
    assert signals.days_remaining == 5
    assert signals.pending_milestones == 2
    assert signals.breached is False
