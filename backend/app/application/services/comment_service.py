import uuid
from datetime import UTC, datetime

from app.application.ports.comment_repository import CommentRepository
from app.domain.entities import Comment


class CommentNotFoundError(Exception):
    pass


class EmptyCommentError(Exception):
    pass


class NotCommentAuthorError(Exception):
    pass


class CommentService:
    def __init__(self, comment_repository: CommentRepository):
        self._comments = comment_repository

    def post_comment(
        self,
        project_id: uuid.UUID,
        body: str,
        *,
        author_id: uuid.UUID | None,
        author_guest_id: uuid.UUID | None,
    ) -> Comment:
        # Belt-and-braces alongside the schema's Field(min_length=1) - a
        # whitespace-only body would pass that check but shouldn't be
        # stored as a real comment.
        stripped = body.strip()
        if not stripped:
            raise EmptyCommentError("A comment can't be empty")
        comment = Comment(
            id=uuid.uuid4(),
            project_id=project_id,
            body=stripped,
            author_id=author_id,
            author_guest_id=author_guest_id,
            created_at=datetime.now(UTC),
        )
        return self._comments.create(comment)

    def list_comments(self, project_id: uuid.UUID) -> list[Comment]:
        return self._comments.list_by_project(project_id)

    def get_comment(self, project_id: uuid.UUID, comment_id: uuid.UUID) -> Comment:
        comment = self._comments.get_by_id(comment_id)
        if comment is None or comment.project_id != project_id:
            raise CommentNotFoundError(f"Comment {comment_id} not found")
        return comment

    def delete_comment(
        self,
        project_id: uuid.UUID,
        comment_id: uuid.UUID,
        *,
        requester_user_id: uuid.UUID | None,
        requester_guest_id: uuid.UUID | None,
        project_owner_id: uuid.UUID,
    ) -> None:
        comment = self.get_comment(project_id, comment_id)
        is_author = (
            requester_user_id is not None and comment.author_id == requester_user_id
        ) or (requester_guest_id is not None and comment.author_guest_id == requester_guest_id)
        is_owner = requester_user_id is not None and requester_user_id == project_owner_id
        if not (is_author or is_owner):
            raise NotCommentAuthorError(
                "Only the author or the project owner can delete this comment"
            )
        self._comments.delete(comment_id)
