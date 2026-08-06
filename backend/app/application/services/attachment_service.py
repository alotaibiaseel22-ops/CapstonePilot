import uuid
from datetime import UTC, datetime

from app.application.ports.attachment_repository import AttachmentRepository
from app.domain.entities import Attachment

MAX_ATTACHMENT_SIZE_BYTES = 20 * 1024 * 1024


class AttachmentNotFoundError(Exception):
    pass


class AttachmentTooLargeError(Exception):
    pass


class NotAttachmentAuthorError(Exception):
    pass


class AttachmentService:
    def __init__(self, attachment_repository: AttachmentRepository):
        self._attachments = attachment_repository

    def upload(
        self,
        project_id: uuid.UUID,
        filename: str,
        content_type: str | None,
        content: bytes,
        *,
        uploader_id: uuid.UUID | None,
        uploader_guest_id: uuid.UUID | None,
    ) -> Attachment:
        if len(content) > MAX_ATTACHMENT_SIZE_BYTES:
            raise AttachmentTooLargeError(
                f"{filename or 'This file'} exceeds the 20MB attachment size limit"
            )
        attachment = Attachment(
            id=uuid.uuid4(),
            project_id=project_id,
            filename=filename or "upload",
            content_type=content_type or "application/octet-stream",
            size_bytes=len(content),
            uploader_id=uploader_id,
            uploader_guest_id=uploader_guest_id,
            created_at=datetime.now(UTC),
        )
        return self._attachments.create(attachment, content)

    def list_attachments(self, project_id: uuid.UUID) -> list[Attachment]:
        return self._attachments.list_by_project(project_id)

    def get_attachment(self, project_id: uuid.UUID, attachment_id: uuid.UUID) -> Attachment:
        """Raises NotFound (not Forbidden) on a project_id mismatch - same
        "don't leak existence across projects" rule GuestService.
        resolve_guest follows, since attachment_id alone isn't URL-scoped
        the way task_id is via _resolve_project_id."""
        attachment = self._attachments.get_by_id(attachment_id)
        if attachment is None or attachment.project_id != project_id:
            raise AttachmentNotFoundError(f"Attachment {attachment_id} not found")
        return attachment

    def get_content(self, attachment_id: uuid.UUID) -> bytes:
        content = self._attachments.get_content(attachment_id)
        if content is None:
            raise AttachmentNotFoundError(f"Attachment {attachment_id} not found")
        return content

    def delete_attachment(
        self,
        project_id: uuid.UUID,
        attachment_id: uuid.UUID,
        *,
        requester_user_id: uuid.UUID | None,
        requester_guest_id: uuid.UUID | None,
        project_owner_id: uuid.UUID,
    ) -> None:
        attachment = self.get_attachment(project_id, attachment_id)
        is_author = (
            requester_user_id is not None and attachment.uploader_id == requester_user_id
        ) or (
            requester_guest_id is not None and attachment.uploader_guest_id == requester_guest_id
        )
        is_owner = requester_user_id is not None and requester_user_id == project_owner_id
        if not (is_author or is_owner):
            raise NotAttachmentAuthorError(
                "Only the uploader or the project owner can delete this attachment"
            )
        self._attachments.delete(attachment_id)
