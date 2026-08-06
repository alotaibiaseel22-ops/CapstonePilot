from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.ports.attachment_repository import AttachmentRepository
from app.domain.entities import Attachment
from app.infrastructure.db.models import AttachmentBlobModel, AttachmentModel


def _as_utc(value: datetime) -> datetime:
    """SQLite drops tzinfo on round-trip, so timestamps written as UTC come
    back naive. Everything this app writes is UTC, so naive == UTC here."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def _to_entity(model: AttachmentModel) -> Attachment:
    return Attachment(
        id=model.id,
        project_id=model.project_id,
        filename=model.filename,
        content_type=model.content_type,
        size_bytes=model.size_bytes,
        uploader_id=model.uploader_id,
        uploader_guest_id=model.uploader_guest_id,
        created_at=_as_utc(model.created_at),
    )


class SqlAlchemyAttachmentRepository(AttachmentRepository):
    def __init__(self, session: Session):
        self._session = session

    def create(self, attachment: Attachment, content: bytes) -> Attachment:
        model = AttachmentModel(
            id=attachment.id,
            project_id=attachment.project_id,
            filename=attachment.filename,
            content_type=attachment.content_type,
            size_bytes=attachment.size_bytes,
            uploader_id=attachment.uploader_id,
            uploader_guest_id=attachment.uploader_guest_id,
            created_at=attachment.created_at,
        )
        self._session.add(model)
        # Explicit flush before adding the blob row: AttachmentModel and
        # AttachmentBlobModel have no ORM relationship() between them (this
        # codebase never declares ORM relationships, only raw FKs), so
        # SQLAlchemy's unit-of-work can't infer their insert order from
        # schema-level FK metadata alone - confirmed empirically that
        # without this, the blob insert can be emitted before the
        # attachment row it references even exists, raising a FOREIGN KEY
        # constraint failure.
        self._session.flush()
        self._session.add(AttachmentBlobModel(attachment_id=attachment.id, content=content))
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def get_by_id(self, attachment_id: UUID) -> Attachment | None:
        model = self._session.get(AttachmentModel, attachment_id)
        return _to_entity(model) if model else None

    def get_content(self, attachment_id: UUID) -> bytes | None:
        blob = self._session.get(AttachmentBlobModel, attachment_id)
        return blob.content if blob else None

    def list_by_project(self, project_id: UUID) -> list[Attachment]:
        # Deliberately queries AttachmentModel only - never joins
        # AttachmentBlobModel, so listing never pulls file bytes over the
        # wire (see AttachmentBlobModel's docstring).
        query = self._session.query(AttachmentModel).filter(
            AttachmentModel.project_id == project_id
        )
        return [_to_entity(model) for model in query.all()]

    def delete(self, attachment_id: UUID) -> None:
        # The blob row is removed by the DB's ON DELETE CASCADE (see the
        # attachment_blobs FK) - SQLite's PRAGMA foreign_keys=ON is already
        # enabled per-connection (session.py), so this is safe in tests too.
        self._session.query(AttachmentModel).filter(AttachmentModel.id == attachment_id).delete()
        self._session.commit()
