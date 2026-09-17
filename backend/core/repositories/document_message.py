from sqlalchemy.orm import Session

from core.models.document_message import DocumentMessage
from core.repositories.base import BaseCRUD
from core.schemas.history import CreateDocumentMessage


class DocumentMessageCRUD(BaseCRUD[DocumentMessage, CreateDocumentMessage]):
    def __init__(self):
        super().__init__(DocumentMessage)

    def list_by_document_id(
        self, db: Session, document_id: str
    ) -> list[DocumentMessage]:
        return (
            db.query(self.model)
            .filter(self.model.document_id == document_id)
            .order_by(self.model.created_at.asc())
            .all()
        )


document_message_crud = DocumentMessageCRUD()
