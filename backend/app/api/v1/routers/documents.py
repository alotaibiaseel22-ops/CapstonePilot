from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.api.schemas.document import DocumentRead
from app.api.v1.deps import get_current_user, get_document_service, require_role
from app.application.services.document_service import (
    DocumentNotFoundError,
    DocumentService,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.domain.entities import User
from app.domain.enums import UserRole

router = APIRouter(tags=["documents"])


@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    project_id: UUID,
    file: UploadFile,
    owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    document_service: DocumentService = Depends(get_document_service),
):
    content = await file.read()
    try:
        document = document_service.upload_document(
            project_id=project_id,
            filename=file.filename,
            content=content,
            uploaded_by=owner.id,
        )
    except (UnsupportedFileTypeError, FileTooLargeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return DocumentRead.model_validate(document)


@router.get("/projects/{project_id}/documents", response_model=list[DocumentRead])
def list_documents(
    project_id: UUID,
    _current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
):
    return [DocumentRead.model_validate(d) for d in document_service.list_documents(project_id)]


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    _owner: User = Depends(require_role(UserRole.PROJECT_OWNER)),
    document_service: DocumentService = Depends(get_document_service),
):
    try:
        document_service.delete_document(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
