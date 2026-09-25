import uuid
from typing import Literal

from pydantic import BaseModel, Field

from core.schemas.document_version import DocumentVersionResponse


class ProposeEditRequest(BaseModel):
    instruction: str = Field(..., min_length=1)
    selection_text: str | None = None
    html: str | None = None
    scope: Literal["selection", "document"] = "selection"
    version_id: uuid.UUID | None = None


class EditPatch(BaseModel):
    id: str
    target: str
    before: str
    after: str
    rationale: str
    status: Literal["pending"] = "pending"
    occurrence: int = 0


class ProposeEditResponse(BaseModel):
    document_id: uuid.UUID
    scope: Literal["selection", "document"]
    instruction: str
    plan: list[str] = Field(default_factory=list)
    patches: list[EditPatch] = Field(default_factory=list)


class ApplyEditRequest(BaseModel):
    before: str = ""
    after: str = ""
    html: str | None = None
    version_id: uuid.UUID | None = None
    change_id: uuid.UUID | None = None
    occurrence: int = 0


class ApplyEditResponse(BaseModel):
    document_id: uuid.UUID
    html: str
    before: str
    after: str
    active_version_id: uuid.UUID | None = None
    versions: list[DocumentVersionResponse] = Field(default_factory=list)
