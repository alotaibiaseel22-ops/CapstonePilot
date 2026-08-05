import uuid
from datetime import UTC, datetime

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base


class GuestModel(Base):
    __tablename__ = "guests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    invitation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("invitations.id", ondelete="CASCADE"), index=True
    )
    display_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
