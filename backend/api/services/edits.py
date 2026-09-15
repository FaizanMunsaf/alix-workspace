import json
import uuid

from fastapi import HTTPException, status

from api.services.documents import get_document, save_document_content
from core.database import get_sync_db_session
from core.repositories import clause_embedding_crud
from core.schemas.edits import (
    ApplyEditResponse,
    EditPatch,
    ProposeEditResponse,
)
from core.utils.edits import PatchConflict, apply_text_patch, parse_llm_json
from ds.rag.embeddings import get_embedding_model
from ds.rag.llms import get_llm

_SELECTION_PROMPT = """You are editing a legal contract. Rewrite ONLY the selected passage.
Do not change unrelated clauses. Keep clause numbering if it appears in the selection.
Return JSON with keys: after (full replacement text), rationale (one sentence).

Instruction:
{instruction}

Selected passage:
{selection}
"""

_DOCUMENT_PROMPT = """You are planning scoped edits to a legal contract.
Use ONLY the candidate clauses below. Do not invent clauses.
If a candidate does not need to change, omit it.
before must be an exact excerpt copied from a candidate.
Return JSON:
{{
  "plan": ["short label of each change"],
  "patches": [
    {{"target": "label", "before": "exact excerpt", "after": "replacement", "rationale": "why"}}
  ]
}}

Instruction:
{instruction}

Candidate clauses:
{clauses}
"""


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
        return _propose_selection(
            document_id, instruction=text, selection=selection_text
        )
    return _propose_document(document_id, instruction=text)


def apply_edit(
    document_id: str,
    *,
    before: str,
    after: str,
    html: str | None,
    version_id: str | None,
) -> ApplyEditResponse:
    detail = get_document(document_id)
    source = html if html is not None else detail.html or ""
    try:
        updated = apply_text_patch(source, before, after)
    except PatchConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    saved = save_document_content(
        document_id,
        html=updated,
        version_id=version_id
        or (str(detail.active_version_id) if detail.active_version_id else None),
    )
    return ApplyEditResponse(
        document_id=saved.document_id,
        html=saved.html or updated,
        before=before,
        after=after,
    )


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
        _SELECTION_PROMPT.format(instruction=instruction, selection=selected)
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
        _DOCUMENT_PROMPT.format(instruction=instruction, clauses=clause_block)
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
