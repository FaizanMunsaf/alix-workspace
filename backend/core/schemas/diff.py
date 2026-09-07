import uuid
from typing import Literal

from pydantic import BaseModel, Field


class DiffRequest(BaseModel):
    from_version_id: uuid.UUID
    to_version_id: uuid.UUID


class DiffChangeResponse(BaseModel):
    status: Literal["added", "deleted", "modified"]
    path: str
    node_type: str
    title: str | None = None
    fields: list[str] = Field(default_factory=list)
    before: dict | None = None
    after: dict | None = None


class ASTDiffResponse(BaseModel):
    added: list[DiffChangeResponse] = Field(default_factory=list)
    deleted: list[DiffChangeResponse] = Field(default_factory=list)
    modified: list[DiffChangeResponse] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)
