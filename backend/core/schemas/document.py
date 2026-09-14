import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from core.schemas.document_version import DocumentVersionResponse


class CreateDocument(BaseModel):
    id: uuid.UUID | None = None
    title: str = Field(..., description="The title of the document")
    document_type: str = Field(..., description="The type of the document")
    status: str = Field(..., description="The status of the document")
    metadata_info: dict = Field(
        default_factory=dict, description="The metadata of the document"
    )


class UpdateDocument(BaseModel):
    title: str | None = None
    document_type: str | None = None
    status: str | None = None
    metadata_info: dict | None = None


class DocumentResponse(BaseModel):
    id: uuid.UUID
    title: str
    document_type: str
    status: str
    metadata_info: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    document_id: uuid.UUID
    version_id: uuid.UUID
    title: str
    status: str
    processing_status: str
    message: str
    filename: str
    file_path: str = Field(exclude=True)


class DocumentListItem(BaseModel):
    document_id: uuid.UUID
    version_id: uuid.UUID | None = None
    title: str
    status: str
    processing_status: str
    version_number: int = 1
    created_at: datetime


class DocumentDetailResponse(BaseModel):
    document_id: uuid.UUID
    title: str
    status: str
    document_type: str
    html: str | None = None
    active_version_id: uuid.UUID | None = None
    versions: list[DocumentVersionResponse]

    model_config = {"from_attributes": True}


class SaveDocumentContent(BaseModel):
    html: str = Field(..., description="TipTap/HTML document body")
    version_id: uuid.UUID | None = None
