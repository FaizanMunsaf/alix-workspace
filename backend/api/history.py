from fastapi import APIRouter

from api.services.edits import apply_edit
from api.services.history import (
    list_document_changes,
    list_document_messages,
    reject_document_change,
)
from core.schemas.edits import ApplyEditResponse
from core.schemas.history import (
    DecideChangeRequest,
    DocumentChangeResponse,
    DocumentMessageResponse,
)

router = APIRouter(prefix="/documents", tags=["History"])


@router.get("/{document_id}/changes", response_model=list[DocumentChangeResponse])
def list_changes(document_id: str):
    return list_document_changes(document_id)


@router.get("/{document_id}/messages", response_model=list[DocumentMessageResponse])
def list_messages(document_id: str):
    return list_document_messages(document_id)


@router.post(
    "/{document_id}/changes/{change_id}/reject",
    response_model=DocumentChangeResponse,
)
def reject_change(document_id: str, change_id: str):
    return reject_document_change(document_id, change_id)


@router.post(
    "/{document_id}/changes/{change_id}/accept",
    response_model=ApplyEditResponse,
)
def accept_change(document_id: str, change_id: str, body: DecideChangeRequest):
    return apply_edit(
        document_id,
        html=body.html,
        change_id=change_id,
    )
