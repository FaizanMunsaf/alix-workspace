from sqlalchemy.orm import Session

from core.models.document_ast_node import DocumentASTNode
from core.repositories.base import BaseCRUD
from core.schemas.document_ast_node import CreateDocumentASTNode


class DocumentASTNodeCRUD(BaseCRUD[DocumentASTNode, CreateDocumentASTNode]):
    def __init__(self):
        super().__init__(DocumentASTNode)

    def create_many(
        self, db: Session, items: list[CreateDocumentASTNode]
    ) -> list[DocumentASTNode]:
        rows = [self.model(**item.model_dump(exclude_none=True)) for item in items]
        db.add_all(rows)
        db.commit()
        for row in rows:
            db.refresh(row)
        return rows


document_ast_node_crud = DocumentASTNodeCRUD()
