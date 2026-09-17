from sqlalchemy.orm import Session

from core.models.document_change import DocumentChange
from core.repositories.base import BaseCRUD
from core.schemas.history import CreateDocumentChange


class DocumentChangeCRUD(BaseCRUD[DocumentChange, CreateDocumentChange]):
    def __init__(self):
        super().__init__(DocumentChange)

    def create(self, db: Session, obj_in: CreateDocumentChange):
        data = obj_in.model_dump(exclude_none=True)
        data["before_text"] = data.pop("before", "")
        data["after_text"] = data.pop("after", "")
        db_obj = self.model(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def list_by_document_id(
        self, db: Session, document_id: str
    ) -> list[DocumentChange]:
        return (
            db.query(self.model)
            .filter(self.model.document_id == document_id)
            .order_by(self.model.created_at.desc())
            .all()
        )


document_change_crud = DocumentChangeCRUD()
