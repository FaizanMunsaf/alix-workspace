import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class CreateDocumentChange(BaseModel):
    id: uuid.UUID | None = None
    document_id: uuid.UUID
    version_id: uuid.UUID | None = None
    result_version_id: uuid.UUID | None = None
    actor: Literal["user", "ai"]
    instruction: str | None = None
    target: str
    before: str = ""
    after: str = ""
    rationale: str | None = None
    decision: Literal["pending", "accepted", "rejected"] = "pending"
    decided_at: datetime | None = None


class UpdateDocumentChange(BaseModel):
    result_version_id: uuid.UUID | None = None
    decision: Literal["pending", "accepted", "rejected"] | None = None
    decided_at: datetime | None = None


class DocumentChangeResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    version_id: uuid.UUID | None
    result_version_id: uuid.UUID | None
    actor: str
    instruction: str | None
    target: str
    before: str
    after: str
    rationale: str | None
    decision: str
    created_at: datetime
    decided_at: datetime | None

    model_config = {"from_attributes": True}


class CreateDocumentMessage(BaseModel):
    id: uuid.UUID | None = None
    document_id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str


class DocumentMessageResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RestoreVersionRequest(BaseModel):
    version_id: uuid.UUID


class DecideChangeRequest(BaseModel):
    html: str | None = None
