import json
import uuid

from fastapi import HTTPException, status

from api.services.documents import get_document
from api.services.edits import _store_pending_patches
from core.database import get_sync_db_session
from core.repositories.knowledge import knowledge_source_crud
from core.schemas.edits import EditPatch, ProposeEditResponse
from core.schemas.knowledge import (
    GroundedReviewRequest,
    GroundedReviewResponse,
    GroundedSourceCitation,
    KnowledgeSourceResponse,
)
from core.utils.edits import parse_llm_json
from ds.intelligences import format_layer_blocks, retrieve_layered
from ds.rag.embeddings import get_embedding_model
from ds.rag.llms import get_llm
from ds.rag.prompts import load_prompt
from seeds.knowledge_seed import ensure_demo_knowledge

_DEFAULT_INSTRUCTION = (
    "Review this contract against the private negotiation playbooks. "
    "Identify deviations and propose targeted redlines so the contract "
    "aligns with playbook positions (especially liability and confidentiality)."
)


def list_knowledge_sources(
    *, ensure_seed: bool = True
) -> list[KnowledgeSourceResponse]:
    if ensure_seed:
        ensure_demo_knowledge()
    with get_sync_db_session() as db:
        return knowledge_source_crud.list_with_counts(db)


def seed_knowledge(*, force: bool = False) -> dict:
    return ensure_demo_knowledge(force=force)


def review_against_knowledge(
    document_id: str,
    body: GroundedReviewRequest,
) -> GroundedReviewResponse:
    ensure_demo_knowledge()
    get_document(document_id)
    instruction = (body.instruction or "").strip() or _DEFAULT_INSTRUCTION
    document_uuid = uuid.UUID(document_id)

    query_embedding = get_embedding_model().embed_query(instruction)
    with get_sync_db_session() as db:
        hits = retrieve_layered(
            db,
            query_embedding,
            document_id=document_uuid,
            playbook_ids=body.playbook_ids,
            include_public=body.include_public,
            top_k_contract=body.top_k_contract,
            top_k_playbook=body.top_k_playbook,
            top_k_public=body.top_k_public if body.include_public else 0,
        )

    contract_blocks = format_layer_blocks(hits, "contract")
    playbook_blocks = format_layer_blocks(hits, "playbook")
    public_blocks = format_layer_blocks(hits, "public_ref")

    if contract_blocks == "(none)":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No indexed contract clauses found. Wait for ingest to finish.",
        )
    if playbook_blocks == "(none)":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No playbook passages retrieved. Seed knowledge sources first.",
        )

    prompt = load_prompt("grounded_review").format(
        instruction=instruction,
        contract=contract_blocks,
        playbook=playbook_blocks,
        public=public_blocks,
    )
    raw = get_llm().generate_json(prompt, format_schema={"type": "object"})
    try:
        parsed = parse_llm_json(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Grounded review returned invalid JSON.",
        ) from exc
    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Grounded review returned invalid JSON.",
        )

    plan = [str(item) for item in (parsed.get("plan") or []) if str(item).strip()]
    deviations = [
        str(item) for item in (parsed.get("deviations") or []) if str(item).strip()
    ]
    patches: list[EditPatch] = []
    contract_blob = "\n".join(hit.content for hit in hits if hit.layer == "contract")
    for item in parsed.get("patches") or []:
        if not isinstance(item, dict):
            continue
        before = str(item.get("before") or "").strip()
        after = str(item.get("after") or "").strip()
        if not before or after == before:
            continue
        if (
            before not in contract_blob
            and before.casefold() not in contract_blob.casefold()
        ):
            # Strict grounding: only patch text that appears in retrieved contract passages.
            continue
        patches.append(
            EditPatch(
                id=str(uuid.uuid4()),
                target=str(item.get("target") or "Clause").strip() or "Clause",
                before=before,
                after=after,
                rationale=str(item.get("rationale") or "").strip(),
                status="pending",
            )
        )

    stored = _store_pending_patches(
        document_id, instruction=instruction, patches=patches
    )

    citations = [
        GroundedSourceCitation(
            layer=hit.layer,  # type: ignore[arg-type]
            label=hit.label,
            title=hit.title,
            content=hit.content,
        )
        for hit in hits
    ]

    return GroundedReviewResponse(
        document_id=document_uuid,
        instruction=instruction,
        plan=plan,
        deviations=deviations,
        patches=[patch.model_dump() for patch in stored],
        citations=citations,
    )


def propose_response_from_review(
    review: GroundedReviewResponse,
) -> ProposeEditResponse:
    return ProposeEditResponse(
        document_id=review.document_id,
        scope="document",
        instruction=review.instruction,
        plan=review.plan,
        patches=[EditPatch(**patch) for patch in review.patches],
    )
