import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base


class CommentModel(Base):
    __tablename__ = "comments"
    __table_args__ = (
        CheckConstraint(
            "(author_id IS NOT NULL AND author_guest_id IS NULL) OR "
            "(author_id IS NULL AND author_guest_id IS NOT NULL)",
            name="ck_comments_exactly_one_author",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    body: Mapped[str] = mapped_column(Text)
    author_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    # SET NULL, not CASCADE - a departed guest shouldn't take their comments
    # down with them (matches Task.assignee_guest_id's precedent).
    author_guest_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("guests.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
