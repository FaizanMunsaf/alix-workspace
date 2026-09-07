import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CreateDocumentASTNode(BaseModel):
    id: uuid.UUID | None = None
    version_id: uuid.UUID
    parent_id: uuid.UUID | None = None
    node_type: str
    node_index: int
    title: str | None = None
    content: str | None = None
    metadata_info: dict = Field(default_factory=dict)


class UpdateDocumentASTNode(BaseModel):
    parent_id: uuid.UUID | None = None
    node_type: str | None = None
    node_index: int | None = None
    title: str | None = None
    content: str | None = None
    metadata_info: dict | None = None


class DocumentASTNodeResponse(BaseModel):
    id: uuid.UUID
    version_id: uuid.UUID
    parent_id: uuid.UUID | None
    node_type: str
    node_index: int
    title: str | None
    content: str | None
    metadata_info: dict
    created_at: datetime

    model_config = {"from_attributes": True}
