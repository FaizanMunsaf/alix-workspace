from core.models.document_version import DocumentVersion
from core.repositories.base import BaseCRUD
from core.schemas.document_version import CreateDocumentVersion
from sqlalchemy.orm import Session


class DocumentVersionCRUD(BaseCRUD[DocumentVersion, CreateDocumentVersion]):
    def __init__(self):
        super().__init__(DocumentVersion)

    def list_by_document_id(
        self, db: Session, document_id: str
    ) -> list[DocumentVersion]:
        return (
            db.query(self.model)
            .filter(self.model.document_id == document_id)
            .order_by(self.model.version_number.asc())
            .all()
        )


document_version_crud = DocumentVersionCRUD()
