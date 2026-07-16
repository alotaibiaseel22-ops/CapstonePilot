from uuid import UUID

from sqlalchemy.orm import Session

from app.application.ports.project_repository import ProjectRepository
from app.domain.entities import Project
from app.domain.enums import ProjectStatus
from app.infrastructure.db.models import ProjectModel


def _to_entity(model: ProjectModel) -> Project:
    return Project(
        id=model.id,
        name=model.name,
        description=model.description,
        status=ProjectStatus(model.status),
        owner_id=model.owner_id,
        start_date=model.start_date,
        due_date=model.due_date,
        created_at=model.created_at,
    )


class SqlAlchemyProjectRepository(ProjectRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, project_id: UUID) -> Project | None:
        model = self._session.get(ProjectModel, project_id)
        return _to_entity(model) if model else None

    def list_all(self) -> list[Project]:
        return [_to_entity(model) for model in self._session.query(ProjectModel).all()]

    def create(self, project: Project) -> Project:
        model = ProjectModel(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status.value,
            owner_id=project.owner_id,
            start_date=project.start_date,
            due_date=project.due_date,
            created_at=project.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def update(self, project: Project) -> Project:
        model = self._session.get(ProjectModel, project.id)
        if model is None:
            raise ValueError(f"Project {project.id} not found")
        model.name = project.name
        model.description = project.description
        model.status = project.status.value
        model.start_date = project.start_date
        model.due_date = project.due_date
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def delete(self, project_id: UUID) -> None:
        model = self._session.get(ProjectModel, project_id)
        if model is not None:
            self._session.delete(model)
            self._session.commit()
