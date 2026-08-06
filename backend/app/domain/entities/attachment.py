from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Attachment:
    """Metadata only - the file's bytes live in a separate blob row (see
    AttachmentRepository.get_content), fetched only when a download is
    actually requested, so listing attachments never pulls blob data across
    the wire. Unlike Task.assignee_id/assignee_guest_id (which allows both
    null = unassigned), an attachment always has an uploader - exactly one
    of uploader_id/uploader_guest_id is set, never both, never neither
    (enforced in AttachmentService and by a DB check constraint)."""

    id: UUID
    project_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    uploader_id: UUID | None
    uploader_guest_id: UUID | None
    created_at: datetime
