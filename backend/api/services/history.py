from datetime import datetime, timezone

from fastapi import HTTPException, status

from core.database import get_sync_db_session
from core.repositories import document_change_crud, document_crud, document_message_crud
from core.schemas.history import (
    DocumentChangeResponse,
    DocumentMessageResponse,
    UpdateDocumentChange,
)


def list_document_changes(document_id: str) -> list[DocumentChangeResponse]:
    _require_document(document_id)
    with get_sync_db_session() as db:
        rows = document_change_crud.list_by_document_id(db, document_id)
        return [DocumentChangeResponse.model_validate(row) for row in rows]


def list_document_messages(document_id: str) -> list[DocumentMessageResponse]:
    _require_document(document_id)
    with get_sync_db_session() as db:
        rows = document_message_crud.list_by_document_id(db, document_id)
        return [DocumentMessageResponse.model_validate(row) for row in rows]


def reject_document_change(document_id: str, change_id: str) -> DocumentChangeResponse:
    _require_document(document_id)
    with get_sync_db_session() as db:
        change = document_change_crud.get(db, change_id)
        if change is None or str(change.document_id) != document_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Change was not found.",
            )
        if change.decision != "pending":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Change is no longer pending.",
            )
        updated = document_change_crud.update(
            db,
            change_id,
            UpdateDocumentChange(
                decision="rejected",
                decided_at=datetime.now(timezone.utc),
            ),
        )
        return DocumentChangeResponse.model_validate(updated)


def _require_document(document_id: str) -> None:
    with get_sync_db_session() as db:
        if document_crud.get(db, document_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document was not found.",
            )
