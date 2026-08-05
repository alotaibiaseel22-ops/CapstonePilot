from uuid import UUID

from sqlalchemy.orm import Session

from app.application.ports.task_repository import TaskRepository
from app.domain.entities import Task
from app.domain.enums import TaskPriority, TaskStatus
from app.infrastructure.db.models import TaskModel


def _to_entity(model: TaskModel) -> Task:
    return Task(
        id=model.id,
        milestone_id=model.milestone_id,
        title=model.title,
        description=model.description,
        status=TaskStatus(model.status),
        priority=TaskPriority(model.priority),
        assignee_id=model.assignee_id,
        assignee_guest_id=model.assignee_guest_id,
        due_date=model.due_date,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyTaskRepository(TaskRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, task_id: UUID) -> Task | None:
        model = self._session.get(TaskModel, task_id)
        return _to_entity(model) if model else None

    def list_by_milestone(self, milestone_id: UUID) -> list[Task]:
        query = self._session.query(TaskModel).filter(TaskModel.milestone_id == milestone_id)
        return [_to_entity(model) for model in query.all()]

    def create(self, task: Task) -> Task:
        model = TaskModel(
            id=task.id,
            milestone_id=task.milestone_id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            assignee_id=task.assignee_id,
            assignee_guest_id=task.assignee_guest_id,
            due_date=task.due_date,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def update(self, task: Task) -> Task:
        model = self._session.get(TaskModel, task.id)
        if model is None:
            raise ValueError(f"Task {task.id} not found")
        model.title = task.title
        model.description = task.description
        model.status = task.status.value
        model.priority = task.priority.value
        model.assignee_id = task.assignee_id
        model.assignee_guest_id = task.assignee_guest_id
        model.due_date = task.due_date
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def delete(self, task_id: UUID) -> None:
        model = self._session.get(TaskModel, task_id)
        if model is not None:
            self._session.delete(model)
            self._session.commit()
