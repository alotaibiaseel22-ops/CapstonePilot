from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status

from app.api.schemas.attachment import AttachmentRead
from app.api.v1.deps import (
    Actor,
    get_attachment_service,
    get_project_service,
    require_project_access,
)
from app.application.services.attachment_service import (
    AttachmentNotFoundError,
    AttachmentService,
    AttachmentTooLargeError,
    NotAttachmentAuthorError,
)
from app.application.services.project_service import ProjectService

router = APIRouter(tags=["attachments"])


@router.post(
    "/projects/{project_id}/attachments",
    response_model=AttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    project_id: UUID,
    file: UploadFile,
    actor: Actor = Depends(require_project_access()),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    content = await file.read()
    try:
        attachment = attachment_service.upload(
            project_id,
            file.filename,
            file.content_type,
            content,
            uploader_id=actor.user.id if actor.kind == "user" else None,
            uploader_guest_id=actor.guest.id if actor.kind == "guest" else None,
        )
    except AttachmentTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return AttachmentRead.model_validate(attachment)


@router.get("/projects/{project_id}/attachments", response_model=list[AttachmentRead])
def list_attachments(
    project_id: UUID,
    _actor: Actor = Depends(require_project_access()),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    return [
        AttachmentRead.model_validate(a) for a in attachment_service.list_attachments(project_id)
    ]


@router.get("/projects/{project_id}/attachments/{attachment_id}/download")
def download_attachment(
    project_id: UUID,
    attachment_id: UUID,
    _actor: Actor = Depends(require_project_access()),
    attachment_service: AttachmentService = Depends(get_attachment_service),
):
    try:
        attachment = attachment_service.get_attachment(project_id, attachment_id)
        content = attachment_service.get_content(attachment_id)
    except AttachmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    # RFC 5987 filename* alongside a plain ASCII fallback - project
    # filenames realistically won't always be ASCII, and a bare
    # filename="..." header silently mangles/breaks on non-ASCII bytes.
    ascii_fallback = attachment.filename.encode("ascii", "ignore").decode("ascii") or "download"
    disposition = (
        f'attachment; filename="{ascii_fallback}"; '
        f"filename*=UTF-8''{quote(attachment.filename)}"
    )
    return Response(
        content=content,
        media_type=attachment.content_type,
        headers={"Content-Disposition": disposition},
    )


@router.delete(
    "/projects/{project_id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_attachment(
    project_id: UUID,
    attachment_id: UUID,
    actor: Actor = Depends(require_project_access()),
    attachment_service: AttachmentService = Depends(get_attachment_service),
    project_service: ProjectService = Depends(get_project_service),
):
    try:
        project = project_service.get_project(project_id)
        attachment_service.delete_attachment(
            project_id,
            attachment_id,
            requester_user_id=actor.user.id if actor.kind == "user" else None,
            requester_guest_id=actor.guest.id if actor.kind == "guest" else None,
            project_owner_id=project.owner_id,
        )
    except AttachmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotAttachmentAuthorError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
