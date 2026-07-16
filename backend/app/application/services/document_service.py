import uuid
from datetime import UTC, datetime

from app.application.ports.document_repository import DocumentRepository
from app.application.ports.file_storage import FileStorage
from app.domain.entities import Document

ACCEPTED_EXTENSIONS = {"pdf", "docx", "pptx", "txt"}
MAX_SIZE_BYTES = 20 * 1024 * 1024

CONTENT_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "txt": "text/plain",
}


class UnsupportedFileTypeError(Exception):
    pass


class FileTooLargeError(Exception):
    pass


class DocumentNotFoundError(Exception):
    pass


class DocumentService:
    def __init__(self, document_repository: DocumentRepository, file_storage: FileStorage):
        self._documents = document_repository
        self._storage = file_storage

    def upload_document(
        self,
        project_id: uuid.UUID,
        filename: str,
        content: bytes,
        uploaded_by: uuid.UUID,
    ) -> Document:
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if extension not in ACCEPTED_EXTENSIONS:
            allowed = sorted(ACCEPTED_EXTENSIONS)
            raise UnsupportedFileTypeError(f"'.{extension}' is not one of {allowed}")
        if len(content) > MAX_SIZE_BYTES:
            raise FileTooLargeError(f"{filename} exceeds the 20MB limit")

        storage_path = self._storage.save(project_id, filename, content)

        document = Document(
            id=uuid.uuid4(),
            project_id=project_id,
            filename=filename,
            storage_path=storage_path,
            content_type=CONTENT_TYPES[extension],
            size_bytes=len(content),
            detected_language=None,
            uploaded_by=uploaded_by,
            created_at=datetime.now(UTC),
        )
        return self._documents.create(document)

    def list_documents(self, project_id: uuid.UUID) -> list[Document]:
        return self._documents.list_by_project(project_id)

    def delete_document(self, document_id: uuid.UUID) -> None:
        document = self._documents.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(f"Document {document_id} not found")
        self._storage.delete(document.storage_path)
        self._documents.delete(document_id)
