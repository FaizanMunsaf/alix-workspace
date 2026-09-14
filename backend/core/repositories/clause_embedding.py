import uuid

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from core.models.clause_embeddings import ClauseEmbedding
from core.models.document_version import DocumentVersion
from core.repositories.base import BaseCRUD
from core.schemas.clause_embedding import ClauseSearchHit, CreateClauseEmbedding


class ClauseEmbeddingCRUD(BaseCRUD[ClauseEmbedding, CreateClauseEmbedding]):
    def __init__(self):
        super().__init__(ClauseEmbedding)

    def create_many(
        self, db: Session, items: list[CreateClauseEmbedding]
    ) -> list[ClauseEmbedding]:
        rows = [self.model(**item.model_dump(exclude_none=True)) for item in items]
        db.add_all(rows)
        db.commit()
        for row in rows:
            db.refresh(row)
        return rows

    def search_query(
        self,
        query_embedding: list[float],
        *,
        top_k: int,
        document_id: uuid.UUID | None = None,
    ) -> Select:
        distance = self.model.embedding.cosine_distance(query_embedding)
        stmt = (
            select(self.model, DocumentVersion.document_id, distance.label("distance"))
            .join(DocumentVersion, self.model.version_id == DocumentVersion.id)
            .order_by(distance)
            .limit(top_k)
        )
        if document_id is not None:
            stmt = stmt.where(DocumentVersion.document_id == document_id)
        return stmt

    def search(
        self,
        db: Session,
        query_embedding: list[float],
        *,
        top_k: int,
        document_id: uuid.UUID | None = None,
    ) -> list[ClauseSearchHit]:
        stmt = self.search_query(query_embedding, top_k=top_k, document_id=document_id)
        hits: list[ClauseSearchHit] = []
        for embedding, version_document_id, distance in db.execute(stmt):
            hits.append(
                ClauseSearchHit(
                    id=embedding.id,
                    version_id=embedding.version_id,
                    document_id=version_document_id,
                    ast_node_id=embedding.ast_node_id,
                    clause_category=embedding.clause_category,
                    content=embedding.content,
                    distance=float(distance),
                )
            )
        return hits


clause_embedding_crud = ClauseEmbeddingCRUD()
