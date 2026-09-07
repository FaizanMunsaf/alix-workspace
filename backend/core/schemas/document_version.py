import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CreateDocumentVersion(BaseModel):
    id: uuid.UUID | None = None
    document_id: uuid.UUID
    version_number: int = 1
    raw_text: str | None = None
    file_path: str | None = None
    ast_json: dict | None = None
    processing_status: str = Field(default="pending")


class UpdateDocumentVersion(BaseModel):
    raw_text: str | None = None
    file_path: str | None = None
    ast_json: dict | None = None
    processing_status: str | None = None


class DocumentVersionResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    version_number: int
    raw_text: str | None
    file_path: str | None
    processing_status: str
    created_at: datetime

    model_config = {"from_attributes": True}
