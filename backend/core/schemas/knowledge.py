import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SourceLayer = Literal["playbook", "public_ref"]


class CreateKnowledgeSource(BaseModel):
    id: uuid.UUID | None = None
    title: str
    source_layer: SourceLayer
    description: str | None = None


class CreateKnowledgeChunk(BaseModel):
    id: uuid.UUID | None = None
    source_id: uuid.UUID
    chunk_index: int = 0
    content: str
    embedding: list[float]


class KnowledgeChunkHit(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    source_title: str
    source_layer: SourceLayer
    content: str
    distance: float


class KnowledgeSourceResponse(BaseModel):
    id: uuid.UUID
    title: str
    source_layer: SourceLayer
    description: str | None
    chunk_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class GroundedReviewRequest(BaseModel):
    html: str | None = None
    instruction: str | None = None
    playbook_ids: list[uuid.UUID] | None = None
    include_public: bool = True
    top_k_contract: int = Field(default=16, ge=1, le=40)
    top_k_playbook: int = Field(default=8, ge=1, le=20)
    top_k_public: int = Field(default=4, ge=1, le=20)


class GroundedSourceCitation(BaseModel):
    layer: Literal["contract", "playbook", "public_ref"]
    label: str
    title: str | None = None
    content: str


class GroundedReviewResponse(BaseModel):
    document_id: uuid.UUID
    instruction: str
    plan: list[str] = Field(default_factory=list)
    deviations: list[str] = Field(default_factory=list)
    patches: list[dict] = Field(default_factory=list)
    citations: list[GroundedSourceCitation] = Field(default_factory=list)
