from datetime import datetime
import uuid

from pydantic import BaseModel


class CreateClauseEmbedding(BaseModel):
    id: uuid.UUID | None = None
    version_id: uuid.UUID
    ast_node_id: uuid.UUID
    clause_category: str | None = None
    content: str
    embedding: list[float]


class ClauseEmbedInput(BaseModel):
    version_id: uuid.UUID
    ast_node_id: uuid.UUID
    clause_category: str
    content: str


class ClauseSearchHit(BaseModel):
    id: uuid.UUID
    version_id: uuid.UUID
    document_id: uuid.UUID
    ast_node_id: uuid.UUID
    clause_category: str | None = None
    content: str
    distance: float


class ClauseEmbeddingResponse(BaseModel):
    id: uuid.UUID
    version_id: uuid.UUID
    ast_node_id: uuid.UUID
    clause_category: str | None
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
