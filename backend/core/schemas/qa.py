from pydantic import BaseModel, Field


class QARequest(BaseModel):
    query: str
    document_id: str | None = None
    selection: str | None = None
    top_k: int = Field(default=12, ge=1, le=20)


class QASource(BaseModel):
    content: str
    metadata: dict


class QAResponse(BaseModel):
    query: str
    answer: str
    sources: list[QASource]
