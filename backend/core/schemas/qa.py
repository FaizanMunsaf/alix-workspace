from pydantic import BaseModel, Field


class QARequest(BaseModel):
    query: str
    document_id: str | None = None
    top_k: int = Field(default=5, ge=1)
