from uuid import UUID

from sqlalchemy.orm import Session

from app.application.ports.project_member_repository import ProjectMemberRepository
from app.domain.entities import ProjectMember
from app.infrastructure.db.models import ProjectMemberModel


def _to_entity(model: ProjectMemberModel) -> ProjectMember:
    return ProjectMember(
        id=model.id,
        project_id=model.project_id,
        user_id=model.user_id,
        added_at=model.added_at,
    )


class SqlAlchemyProjectMemberRepository(ProjectMemberRepository):
    def __init__(self, session: Session):
        self._session = session

    def add(self, member: ProjectMember) -> ProjectMember:
        model = ProjectMemberModel(
            id=member.id,
            project_id=member.project_id,
            user_id=member.user_id,
            added_at=member.added_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def list_by_project(self, project_id: UUID) -> list[ProjectMember]:
        query = self._session.query(ProjectMemberModel).filter(
            ProjectMemberModel.project_id == project_id
        )
        return [_to_entity(model) for model in query.all()]

    def list_by_user(self, user_id: UUID) -> list[ProjectMember]:
        query = self._session.query(ProjectMemberModel).filter(
            ProjectMemberModel.user_id == user_id
        )
        return [_to_entity(model) for model in query.all()]

    def exists(self, project_id: UUID, user_id: UUID) -> bool:
        query = self._session.query(ProjectMemberModel).filter(
            ProjectMemberModel.project_id == project_id,
            ProjectMemberModel.user_id == user_id,
        )
        return self._session.query(query.exists()).scalar()

    def remove(self, project_id: UUID, user_id: UUID) -> None:
        model = (
            self._session.query(ProjectMemberModel)
            .filter(
                ProjectMemberModel.project_id == project_id,
                ProjectMemberModel.user_id == user_id,
            )
            .first()
        )
        if model is not None:
            self._session.delete(model)
            self._session.commit()

    def delete_by_project(self, project_id: UUID) -> None:
        self._session.query(ProjectMemberModel).filter(
            ProjectMemberModel.project_id == project_id
        ).delete()
        self._session.commit()
