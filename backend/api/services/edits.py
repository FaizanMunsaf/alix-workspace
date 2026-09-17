import json
import uuid

from fastapi import HTTPException, status

from api.services.documents import create_checkpoint, get_document
from core.database import get_sync_db_session
from core.repositories import (
    clause_embedding_crud,
    document_change_crud,
    document_version_crud,
)
from core.schemas.edits import (
    ApplyEditResponse,
    EditPatch,
    ProposeEditResponse,
)
from core.schemas.history import CreateDocumentChange
from core.utils.edits import PatchConflict, apply_text_patch, parse_llm_json
from ds.rag.embeddings import get_embedding_model
from ds.rag.llms import get_llm
from ds.rag.prompts import load_prompt


def propose_edits(
    document_id: str,
    *,
    instruction: str,
    selection_text: str | None,
    html: str | None,
    scope: str,
) -> ProposeEditResponse:
    text = instruction.strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="instruction is required.",
        )
    get_document(document_id)

    if scope == "selection":
        result = _propose_selection(
            document_id, instruction=text, selection=selection_text
        )
    else:
        result = _propose_document(document_id, instruction=text)
    result.patches = _store_pending_patches(
        document_id, instruction=result.instruction, patches=result.patches
    )
    return result


def apply_edit(
    document_id: str,
    *,
    html: str | None,
    version_id: str | None = None,
    change_id: str | None = None,
    before: str | None = None,
    after: str | None = None,
) -> ApplyEditResponse:
    detail = get_document(document_id)
    instruction = "AI edit"
    target = "Clause"
    rationale = None
    actor: str = "ai"

    if change_id:
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
            before = change.before
            after = change.after
            instruction = change.instruction or instruction
            target = change.target
            rationale = change.rationale
            actor = change.actor if change.actor in {"user", "ai"} else "ai"
    elif not (before or "").strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="before is required when change_id is not provided.",
        )

    source = html if html is not None else detail.html or ""
    try:
        updated = apply_text_patch(source, before or "", after or "")
    except PatchConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    saved = create_checkpoint(
        document_id,
        html=updated,
        actor=actor,  # type: ignore[arg-type]
        instruction=instruction,
        target=target,
        before=before or "",
        after=after or "",
        rationale=rationale,
        change_id=change_id,
    )
    return ApplyEditResponse(
        document_id=saved.document_id,
        html=saved.html or updated,
        before=before or "",
        after=after or "",
        active_version_id=saved.active_version_id,
        versions=saved.versions,
    )


def _store_pending_patches(
    document_id: str, instruction: str, patches: list[EditPatch]
) -> list[EditPatch]:
    if not patches:
        return patches
    with get_sync_db_session() as db:
        versions = document_version_crud.list_by_document_id(db, document_id)
        latest = versions[-1] if versions else None
        stored: list[EditPatch] = []
        for patch in patches:
            row = document_change_crud.create(
                db,
                CreateDocumentChange(
                    document_id=uuid.UUID(document_id),
                    version_id=latest.id if latest else None,
                    actor="ai",
                    instruction=instruction,
                    target=patch.target,
                    before=patch.before,
                    after=patch.after,
                    rationale=patch.rationale,
                    decision="pending",
                ),
            )
            stored.append(
                EditPatch(
                    id=str(row.id),
                    target=row.target,
                    before=row.before,
                    after=row.after,
                    rationale=row.rationale or "",
                    status="pending",
                )
            )
        return stored


def _propose_selection(
    document_id: str, *, instruction: str, selection: str | None
) -> ProposeEditResponse:
    selected = (selection or "").strip()
    if not selected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Select a clause or passage before asking for a scoped edit.",
        )
    payload = _llm_json(
        load_prompt("edit_selection").format(
            instruction=instruction, selection=selected
        )
    )
    after = str(payload.get("after") or "").strip()
    if not after:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The model did not return a replacement.",
        )
    rationale = str(
        payload.get("rationale") or "Scoped replacement for the selected text."
    )
    patch = EditPatch(
        id=str(uuid.uuid4()),
        target="Selected text",
        before=selected,
        after=after,
        rationale=rationale,
    )
    return ProposeEditResponse(
        document_id=uuid.UUID(document_id),
        scope="selection",
        instruction=instruction,
        plan=["Selected passage"],
        patches=[patch],
    )


def _propose_document(document_id: str, *, instruction: str) -> ProposeEditResponse:
    try:
        document_uuid = uuid.UUID(document_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="document_id is not a valid UUID.",
        ) from exc

    query_embedding = get_embedding_model().embed_query(instruction)
    with get_sync_db_session() as db:
        hits = clause_embedding_crud.search(
            db,
            query_embedding,
            top_k=8,
            document_id=document_uuid,
        )
    if not hits:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No indexed clauses were found for this document.",
        )
    clause_block = "\n\n".join(
        f"- [{hit.clause_category}] {hit.content}" for hit in hits
    )
    payload = _llm_json(
        load_prompt("edit_document").format(
            instruction=instruction, clauses=clause_block
        )
    )
    raw_patches = payload.get("patches") or []
    allowed = [hit.content for hit in hits]
    patches: list[EditPatch] = []
    for item in raw_patches:
        before = str(item.get("before") or "").strip()
        after = str(item.get("after") or "").strip()
        if not before or not after or before == after:
            continue
        if not any(before in clause for clause in allowed):
            continue
        patches.append(
            EditPatch(
                id=str(uuid.uuid4()),
                target=str(item.get("target") or "Clause"),
                before=before,
                after=after,
                rationale=str(item.get("rationale") or ""),
            )
        )
    plan = [str(label) for label in (payload.get("plan") or []) if str(label).strip()]
    if not plan:
        plan = [patch.target for patch in patches]
    return ProposeEditResponse(
        document_id=document_uuid,
        scope="document",
        instruction=instruction,
        plan=plan,
        patches=patches,
    )


def _llm_json(prompt: str) -> dict:
    raw = get_llm().generate_json(prompt, format_schema={"type": "object"})
    try:
        parsed = parse_llm_json(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The model did not return valid JSON.",
        ) from exc
    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The model did not return valid JSON.",
        )
    return parsed
