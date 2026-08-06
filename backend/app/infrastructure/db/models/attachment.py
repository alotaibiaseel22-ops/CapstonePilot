import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, LargeBinary, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base


class AttachmentModel(Base):
    __tablename__ = "attachments"
    __table_args__ = (
        CheckConstraint(
            "(uploader_id IS NOT NULL AND uploader_guest_id IS NULL) OR "
            "(uploader_id IS NULL AND uploader_guest_id IS NOT NULL)",
            name="ck_attachments_exactly_one_uploader",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(Integer)
    uploader_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    # SET NULL, not CASCADE - a departed guest shouldn't take their uploads
    # down with them (matches Task.assignee_guest_id's precedent).
    uploader_guest_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("guests.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class AttachmentBlobModel(Base):
    """Split from AttachmentModel so listing attachments never pulls file
    bytes across the wire - a plain query against AttachmentModel alone
    (no join) can never accidentally drag a 20MB row along with it."""

    __tablename__ = "attachment_blobs"

    attachment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("attachments.id", ondelete="CASCADE"), primary_key=True
    )
    content: Mapped[bytes] = mapped_column(LargeBinary)
