from core.models.document_version import DocumentVersion
from core.repositories.base import BaseCRUD
from core.schemas.document_version import CreateDocumentVersion


class DocumentVersionCRUD(BaseCRUD[DocumentVersion, CreateDocumentVersion]):
    def __init__(self):
        super().__init__(DocumentVersion)


document_version_crud = DocumentVersionCRUD()
