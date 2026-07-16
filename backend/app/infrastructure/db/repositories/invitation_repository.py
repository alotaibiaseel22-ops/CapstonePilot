from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.ports.invitation_repository import InvitationRepository
from app.domain.entities import Invitation
from app.domain.enums import InvitationStatus
from app.infrastructure.db.models import InvitationModel


def _as_utc(value: datetime | None) -> datetime | None:
    """SQLite drops tzinfo on round-trip, so timestamps written as UTC come
    back naive. Everything this app writes is UTC, so naive == UTC here."""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _to_entity(model: InvitationModel) -> Invitation:
    return Invitation(
        id=model.id,
        project_id=model.project_id,
        email=model.email,
        token=model.token,
        status=InvitationStatus(model.status),
        invited_by=model.invited_by,
        created_at=model.created_at,
        accepted_at=model.accepted_at,
        accepted_by=model.accepted_by,
        expires_at=_as_utc(model.expires_at),
    )


class SqlAlchemyInvitationRepository(InvitationRepository):
    def __init__(self, session: Session):
        self._session = session

    def create(self, invitation: Invitation) -> Invitation:
        model = InvitationModel(
            id=invitation.id,
            project_id=invitation.project_id,
            email=invitation.email,
            token=invitation.token,
            status=invitation.status.value,
            invited_by=invitation.invited_by,
            created_at=invitation.created_at,
            accepted_at=invitation.accepted_at,
            accepted_by=invitation.accepted_by,
            expires_at=invitation.expires_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def get_by_id(self, invitation_id: UUID) -> Invitation | None:
        model = self._session.get(InvitationModel, invitation_id)
        return _to_entity(model) if model else None

    def get_by_token(self, token: str) -> Invitation | None:
        model = self._session.query(InvitationModel).filter(InvitationModel.token == token).first()
        return _to_entity(model) if model else None

    def list_by_project(self, project_id: UUID) -> list[Invitation]:
        query = self._session.query(InvitationModel).filter(
            InvitationModel.project_id == project_id
        )
        ordered = query.order_by(InvitationModel.created_at.desc())
        return [_to_entity(model) for model in ordered.all()]

    def get_active_link_invitation(self, project_id: UUID) -> Invitation | None:
        model = (
            self._session.query(InvitationModel)
            .filter(
                InvitationModel.project_id == project_id,
                InvitationModel.email.is_(None),
                InvitationModel.status == InvitationStatus.PENDING.value,
            )
            .first()
        )
        return _to_entity(model) if model else None

    def list_pending_by_email(self, email: str) -> list[Invitation]:
        query = self._session.query(InvitationModel).filter(
            InvitationModel.email == email,
            InvitationModel.status == InvitationStatus.PENDING.value,
        )
        return [_to_entity(model) for model in query.all()]

    def update(self, invitation: Invitation) -> Invitation:
        model = self._session.get(InvitationModel, invitation.id)
        if model is None:
            raise ValueError(f"Invitation {invitation.id} not found")
        model.status = invitation.status.value
        model.accepted_at = invitation.accepted_at
        model.accepted_by = invitation.accepted_by
        model.expires_at = invitation.expires_at
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def delete_by_project(self, project_id: UUID) -> None:
        self._session.query(InvitationModel).filter(
            InvitationModel.project_id == project_id
        ).delete()
        self._session.commit()
