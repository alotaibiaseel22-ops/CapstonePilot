from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.ports.guest_repository import GuestRepository
from app.domain.entities import Guest
from app.infrastructure.db.models import GuestModel


def _as_utc(value: datetime) -> datetime:
    """SQLite drops tzinfo on round-trip, so timestamps written as UTC come
    back naive. Everything this app writes is UTC, so naive == UTC here."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def _to_entity(model: GuestModel) -> Guest:
    return Guest(
        id=model.id,
        project_id=model.project_id,
        invitation_id=model.invitation_id,
        display_name=model.display_name,
        created_at=_as_utc(model.created_at),
    )


class SqlAlchemyGuestRepository(GuestRepository):
    def __init__(self, session: Session):
        self._session = session

    def create(self, guest: Guest) -> Guest:
        model = GuestModel(
            id=guest.id,
            project_id=guest.project_id,
            invitation_id=guest.invitation_id,
            display_name=guest.display_name,
            created_at=guest.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def get_by_id(self, guest_id: UUID) -> Guest | None:
        model = self._session.get(GuestModel, guest_id)
        return _to_entity(model) if model else None
