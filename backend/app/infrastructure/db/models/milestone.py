import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Date, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base


class MilestoneModel(Base):
    __tablename__ = "milestones"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("plans.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
