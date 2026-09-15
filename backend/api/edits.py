from fastapi import APIRouter

from api.services.edits import apply_edit, propose_edits
from core.schemas.edits import (
    ApplyEditRequest,
    ApplyEditResponse,
    ProposeEditRequest,
    ProposeEditResponse,
)

router = APIRouter(prefix="/documents", tags=["Edits"])


@router.post("/{document_id}/edits/propose", response_model=ProposeEditResponse)
def propose_document_edits(document_id: str, body: ProposeEditRequest):
    return propose_edits(
        document_id,
        instruction=body.instruction,
        selection_text=body.selection_text,
        html=body.html,
        scope=body.scope,
    )


@router.post("/{document_id}/edits/apply", response_model=ApplyEditResponse)
def apply_document_edit(document_id: str, body: ApplyEditRequest):
    return apply_edit(
        document_id,
        before=body.before,
        after=body.after,
        html=body.html,
        version_id=str(body.version_id) if body.version_id else None,
    )
