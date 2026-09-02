from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.services.qa import answer_question

router = APIRouter(prefix="/qa", tags=["Q/A"])


class QARequest(BaseModel):
    query: str
    document_id: str | None = None
    top_k: int = Field(default=5, ge=1)


@router.post("/")
def qa(body: QARequest):
    return answer_question(
        query=body.query,
        document_id=body.document_id,
        top_k=body.top_k,
    )
