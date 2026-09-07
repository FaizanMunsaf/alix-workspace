from fastapi import APIRouter

from api.services.qa import answer_question
from core.schemas.qa import QARequest

router = APIRouter(prefix="/qa", tags=["Q/A"])


@router.post("/")
def qa(body: QARequest):
    return answer_question(
        query=body.query,
        document_id=body.document_id,
        top_k=body.top_k,
    )
