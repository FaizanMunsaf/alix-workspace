from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from core.repositories import clause_embedding_crud
from core.repositories.knowledge import knowledge_chunk_crud
from core.schemas.clause_embedding import ClauseSearchHit
from core.schemas.knowledge import KnowledgeChunkHit


@dataclass
class LayeredHit:
    layer: str  # contract | playbook | public_ref
    label: str
    title: str | None
    content: str
    distance: float


def retrieve_layered(
    db: Session,
    query_embedding: list[float],
    *,
    document_id: uuid.UUID | None,
    playbook_ids: list[uuid.UUID] | None = None,
    include_public: bool = True,
    top_k_contract: int = 12,
    top_k_playbook: int = 8,
    top_k_public: int = 4,
) -> list[LayeredHit]:
    hits: list[LayeredHit] = []

    if document_id is not None and top_k_contract > 0:
        contract_hits: list[ClauseSearchHit] = clause_embedding_crud.search(
            db,
            query_embedding,
            top_k=top_k_contract,
            document_id=document_id,
        )
        for index, hit in enumerate(contract_hits, start=1):
            hits.append(
                LayeredHit(
                    layer="contract",
                    label=f"Contract {index}",
                    title=hit.clause_category,
                    content=hit.content,
                    distance=hit.distance,
                )
            )

    if top_k_playbook > 0:
        playbook_hits: list[KnowledgeChunkHit] = knowledge_chunk_crud.search(
            db,
            query_embedding,
            top_k=top_k_playbook,
            source_layer="playbook",
            source_ids=playbook_ids,
        )
        for index, hit in enumerate(playbook_hits, start=1):
            hits.append(
                LayeredHit(
                    layer="playbook",
                    label=f"Playbook {index}",
                    title=hit.source_title,
                    content=hit.content,
                    distance=hit.distance,
                )
            )

    if include_public and top_k_public > 0:
        public_hits: list[KnowledgeChunkHit] = knowledge_chunk_crud.search(
            db,
            query_embedding,
            top_k=top_k_public,
            source_layer="public_ref",
        )
        for index, hit in enumerate(public_hits, start=1):
            hits.append(
                LayeredHit(
                    layer="public_ref",
                    label=f"Public {index}",
                    title=hit.source_title,
                    content=hit.content,
                    distance=hit.distance,
                )
            )

    return hits


def format_layer_blocks(hits: list[LayeredHit], layer: str) -> str:
    blocks = [
        f"[{hit.label}] ({hit.title or layer})\n{hit.content.strip()}"
        for hit in hits
        if hit.layer == layer and hit.content.strip()
    ]
    return "\n\n".join(blocks) if blocks else "(none)"
