from core.models.documents import Document
from core.repositories.base import BaseCRUD
from core.schemas.document import CreateDocument


class DocumentCRUD(BaseCRUD[Document, CreateDocument]):
    def __init__(self):
        super().__init__(Document)


document_crud = DocumentCRUD()
