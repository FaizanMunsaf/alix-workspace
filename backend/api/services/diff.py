from fastapi import HTTPException, status

from core.database import get_sync_db_session
from core.ast.diff import diff_ast
from core.repositories import document_version_crud
from core.schemas.diff import ASTDiffResponse


def diff_document_versions(from_version_id: str, to_version_id: str) -> ASTDiffResponse:
    with get_sync_db_session() as db:
        old = document_version_crud.get(db, from_version_id)
        new = document_version_crud.get(db, to_version_id)
        if old is None or new is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both document versions were not found.",
            )
        if not old.ast_json or not new.ast_json:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Both versions must be parsed before they can be compared.",
            )
        result = diff_ast(old.ast_json, new.ast_json)
    return ASTDiffResponse.model_validate(result.to_dict())
