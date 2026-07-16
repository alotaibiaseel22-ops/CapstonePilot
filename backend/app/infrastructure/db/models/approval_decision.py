import uuid
from datetime import UTC, datetime

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base


class ApprovalDecisionModel(Base):
    __tablename__ = "approval_decisions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    decided_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(16))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
