import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from core.models.knowledge_chunk import KnowledgeChunk
from core.models.knowledge_source import KnowledgeSource
from core.repositories.base import BaseCRUD
from core.schemas.knowledge import (
    CreateKnowledgeChunk,
    CreateKnowledgeSource,
    KnowledgeChunkHit,
    KnowledgeSourceResponse,
)


class KnowledgeSourceCRUD(BaseCRUD[KnowledgeSource, CreateKnowledgeSource]):
    def __init__(self):
        super().__init__(KnowledgeSource)

    def list_with_counts(self, db: Session) -> list[KnowledgeSourceResponse]:
        chunk_count = func.count(KnowledgeChunk.id)
        stmt = (
            select(KnowledgeSource, chunk_count)
            .outerjoin(KnowledgeChunk, KnowledgeChunk.source_id == KnowledgeSource.id)
            .group_by(KnowledgeSource.id)
            .order_by(KnowledgeSource.source_layer.asc(), KnowledgeSource.title.asc())
        )
        rows: list[KnowledgeSourceResponse] = []
        for source, count in db.execute(stmt):
            rows.append(
                KnowledgeSourceResponse(
                    id=source.id,
                    title=source.title,
                    source_layer=source.source_layer,
                    description=source.description,
                    chunk_count=int(count or 0),
                    created_at=source.created_at,
                )
            )
        return rows


class KnowledgeChunkCRUD(BaseCRUD[KnowledgeChunk, CreateKnowledgeChunk]):
    def __init__(self):
        super().__init__(KnowledgeChunk)

    def create_many(
        self, db: Session, items: list[CreateKnowledgeChunk]
    ) -> list[KnowledgeChunk]:
        rows = [self.model(**item.model_dump(exclude_none=True)) for item in items]
        db.add_all(rows)
        db.commit()
        for row in rows:
            db.refresh(row)
        return rows

    def delete_for_source(self, db: Session, source_id: uuid.UUID) -> None:
        rows = db.execute(
            select(self.model).where(self.model.source_id == source_id)
        ).scalars()
        for row in rows:
            db.delete(row)
        db.commit()

    def search_query(
        self,
        query_embedding: list[float],
        *,
        top_k: int,
        source_layer: str | None = None,
        source_ids: list[uuid.UUID] | None = None,
    ) -> Select:
        distance = self.model.embedding.cosine_distance(query_embedding)
        stmt = (
            select(
                self.model,
                KnowledgeSource.title,
                KnowledgeSource.source_layer,
                distance.label("distance"),
            )
            .join(KnowledgeSource, self.model.source_id == KnowledgeSource.id)
            .order_by(distance)
            .limit(top_k)
        )
        if source_layer is not None:
            stmt = stmt.where(KnowledgeSource.source_layer == source_layer)
        if source_ids:
            stmt = stmt.where(self.model.source_id.in_(source_ids))
        return stmt

    def search(
        self,
        db: Session,
        query_embedding: list[float],
        *,
        top_k: int,
        source_layer: str | None = None,
        source_ids: list[uuid.UUID] | None = None,
    ) -> list[KnowledgeChunkHit]:
        stmt = self.search_query(
            query_embedding,
            top_k=top_k,
            source_layer=source_layer,
            source_ids=source_ids,
        )
        hits: list[KnowledgeChunkHit] = []
        for chunk, title, layer, distance in db.execute(stmt):
            hits.append(
                KnowledgeChunkHit(
                    id=chunk.id,
                    source_id=chunk.source_id,
                    source_title=title,
                    source_layer=layer,
                    content=chunk.content,
                    distance=float(distance),
                )
            )
        return hits


knowledge_source_crud = KnowledgeSourceCRUD()
knowledge_chunk_crud = KnowledgeChunkCRUD()
