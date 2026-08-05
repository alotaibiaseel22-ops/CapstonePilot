import uuid
from datetime import UTC, date, datetime

from app.application.ports.task_repository import TaskRepository
from app.domain.entities import Task
from app.domain.enums import TaskPriority, TaskStatus


class TaskNotFoundError(Exception):
    pass


class NotTaskAssigneeError(Exception):
    pass


class TaskService:
    def __init__(self, task_repository: TaskRepository):
        self._tasks = task_repository

    def create_task(
        self,
        milestone_id: uuid.UUID,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        assignee_id: uuid.UUID | None = None,
        assignee_guest_id: uuid.UUID | None = None,
        due_date: date | None = None,
    ) -> Task:
        now = datetime.now(UTC)
        task = Task(
            id=uuid.uuid4(),
            milestone_id=milestone_id,
            title=title,
            description=description,
            status=TaskStatus.PENDING,
            priority=priority,
            # A task is assigned to a real User or a Guest, never both - if
            # somehow both are given, the User wins and the guest is
            # dropped, matching update_task's clearing behavior below.
            assignee_id=assignee_id,
            assignee_guest_id=None if assignee_id is not None else assignee_guest_id,
            due_date=due_date,
            created_at=now,
            updated_at=now,
        )
        return self._tasks.create(task)

    def list_tasks(self, milestone_id: uuid.UUID) -> list[Task]:
        return self._tasks.list_by_milestone(milestone_id)

    def get_task(self, task_id: uuid.UUID) -> Task:
        task = self._tasks.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task {task_id} not found")
        return task

    def update_task(
        self,
        task_id: uuid.UUID,
        title: str | None = None,
        description: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        assignee_id: uuid.UUID | None = None,
        assignee_guest_id: uuid.UUID | None = None,
        due_date: date | None = None,
    ) -> Task:
        task = self.get_task(task_id)
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if status is not None:
            task.status = status
        if priority is not None:
            task.priority = priority
        # Assigning to one type of assignee clears the other, so the
        # "never both" invariant (also enforced by a DB check constraint)
        # holds without needing a hard validation error on the common case
        # of reassigning a task from a guest to a real member or back.
        if assignee_id is not None:
            task.assignee_id = assignee_id
            task.assignee_guest_id = None
        if assignee_guest_id is not None:
            task.assignee_guest_id = assignee_guest_id
            task.assignee_id = None
        if due_date is not None:
            task.due_date = due_date
        return self._tasks.update(task)

    def update_status_as_guest(
        self, task_id: uuid.UUID, guest_id: uuid.UUID, status: TaskStatus
    ) -> Task:
        """A guest may move the status of ONLY a task assigned to them -
        nothing else about it, and never another task. Everything else a
        task can have changed (title, description, priority, assignee, due
        date) stays exclusively reachable through update_task, which only
        real project members/owners can call (see tasks.py's route gating)."""
        task = self.get_task(task_id)
        if task.assignee_guest_id != guest_id:
            raise NotTaskAssigneeError("This task is not assigned to you")
        task.status = status
        return self._tasks.update(task)

    def delete_task(self, task_id: uuid.UUID) -> None:
        self._tasks.delete(task_id)
