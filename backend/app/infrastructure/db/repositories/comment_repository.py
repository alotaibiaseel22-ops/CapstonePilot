from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.ports.comment_repository import CommentRepository
from app.domain.entities import Comment
from app.infrastructure.db.models import CommentModel


def _as_utc(value: datetime) -> datetime:
    """SQLite drops tzinfo on round-trip, so timestamps written as UTC come
    back naive. Everything this app writes is UTC, so naive == UTC here."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def _to_entity(model: CommentModel) -> Comment:
    return Comment(
        id=model.id,
        project_id=model.project_id,
        body=model.body,
        author_id=model.author_id,
        author_guest_id=model.author_guest_id,
        created_at=_as_utc(model.created_at),
    )


class SqlAlchemyCommentRepository(CommentRepository):
    def __init__(self, session: Session):
        self._session = session

    def create(self, comment: Comment) -> Comment:
        model = CommentModel(
            id=comment.id,
            project_id=comment.project_id,
            body=comment.body,
            author_id=comment.author_id,
            author_guest_id=comment.author_guest_id,
            created_at=comment.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def get_by_id(self, comment_id: UUID) -> Comment | None:
        model = self._session.get(CommentModel, comment_id)
        return _to_entity(model) if model else None

    def list_by_project(self, project_id: UUID) -> list[Comment]:
        # Oldest-first - a chronological discussion thread, distinct from
        # the Activity feed's newest-first "recent events" convention.
        query = (
            self._session.query(CommentModel)
            .filter(CommentModel.project_id == project_id)
            .order_by(CommentModel.created_at)
        )
        return [_to_entity(model) for model in query.all()]

    def delete(self, comment_id: UUID) -> None:
        self._session.query(CommentModel).filter(CommentModel.id == comment_id).delete()
        self._session.commit()
