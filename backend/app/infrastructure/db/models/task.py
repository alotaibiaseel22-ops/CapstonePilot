import uuid
from datetime import UTC, date, datetime

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base


class TaskModel(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "assignee_id IS NULL OR assignee_guest_id IS NULL", name="ck_tasks_single_assignee"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    milestone_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("milestones.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32))
    priority: Mapped[str] = mapped_column(String(16))
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    # Mutually exclusive with assignee_id (see the check constraint above and
    # TaskService's application-level enforcement) - a task assigned to a
    # Guest instead of a real User. SET NULL, not CASCADE: a task must
    # survive even if its guest-assignee record is ever removed.
    assignee_guest_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("guests.id", ondelete="SET NULL"), nullable=True
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
