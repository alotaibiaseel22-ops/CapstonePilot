import uuid
from datetime import UTC, date, datetime

from app.application.ports.task_repository import TaskRepository
from app.domain.entities import Task
from app.domain.enums import TaskPriority, TaskStatus


class TaskNotFoundError(Exception):
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
            assignee_id=assignee_id,
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
        if assignee_id is not None:
            task.assignee_id = assignee_id
        if due_date is not None:
            task.due_date = due_date
        return self._tasks.update(task)

    def delete_task(self, task_id: uuid.UUID) -> None:
        self._tasks.delete(task_id)
