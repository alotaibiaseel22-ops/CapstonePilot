from uuid import UUID

from sqlalchemy.orm import Session

from app.application.ports.document_repository import DocumentRepository
from app.domain.entities import Document
from app.domain.enums import Language
from app.infrastructure.db.models import DocumentModel


def _to_entity(model: DocumentModel) -> Document:
    return Document(
        id=model.id,
        project_id=model.project_id,
        filename=model.filename,
        storage_path=model.storage_path,
        content_type=model.content_type,
        size_bytes=model.size_bytes,
        detected_language=Language(model.detected_language) if model.detected_language else None,
        uploaded_by=model.uploaded_by,
        created_at=model.created_at,
    )


class SqlAlchemyDocumentRepository(DocumentRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, document_id: UUID) -> Document | None:
        model = self._session.get(DocumentModel, document_id)
        return _to_entity(model) if model else None

    def list_by_project(self, project_id: UUID) -> list[Document]:
        query = self._session.query(DocumentModel).filter(DocumentModel.project_id == project_id)
        return [_to_entity(model) for model in query.all()]

    def create(self, document: Document) -> Document:
        model = DocumentModel(
            id=document.id,
            project_id=document.project_id,
            filename=document.filename,
            storage_path=document.storage_path,
            content_type=document.content_type,
            size_bytes=document.size_bytes,
            detected_language=(
                document.detected_language.value if document.detected_language else None
            ),
            uploaded_by=document.uploaded_by,
            created_at=document.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return _to_entity(model)

    def delete(self, document_id: UUID) -> None:
        model = self._session.get(DocumentModel, document_id)
        if model is not None:
            self._session.delete(model)
            self._session.commit()
