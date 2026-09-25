import uuid

from fastapi import HTTPException

from core.database import get_sync_db_session
from core.repositories import (
    clause_embedding_crud,
    document_crud,
    document_message_crud,
)
from core.schemas.clause_embedding import ClauseSearchHit
from core.schemas.history import CreateDocumentMessage
from ds.rag.embeddings import get_embedding_model
from ds.rag.llms import get_llm


def answer_question(
    *,
    query: str,
    document_id: str | None,
    top_k: int,
    selection: str | None = None,
) -> dict:
    if not query.strip():
        raise HTTPException(status_code=400, detail="query is required.")

    document_uuid = None
    if document_id:
        try:
            document_uuid = uuid.UUID(document_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail="document_id is not a valid UUID."
            ) from exc

    focus = (selection or "").strip()
    search_text = query.strip()
    if focus:
        search_text = f"{search_text}\n\nFocus passage:\n{focus}"

    # Leave room for the selected passage as Source 0 when present.
    retrieve_k = max(1, top_k - 1) if focus else top_k

    query_embedding = get_embedding_model().embed_query(search_text)
    with get_sync_db_session() as db:
        hits = clause_embedding_crud.search(
            db,
            query_embedding,
            top_k=retrieve_k,
            document_id=document_uuid,
        )

    context_blocks = _format_context(hits, selection=focus)
    answer = get_llm().generate(
        query.strip(),
        context_blocks,
        selection=focus or None,
    )

    if document_uuid is not None:
        _store_turn(document_uuid, query=query.strip(), answer=answer)

    sources: list[dict] = []
    if focus:
        sources.append(
            {
                "content": focus,
                "metadata": {
                    "document_id": document_id,
                    "clause_category": "selection",
                    "label": "Selected",
                },
            }
        )
    sources.extend(
        {
            "content": hit.content,
            "metadata": {
                "document_id": str(hit.document_id),
                "version_id": str(hit.version_id),
                "ast_node_id": str(hit.ast_node_id),
                "clause_category": hit.clause_category,
                "distance": hit.distance,
                "label": f"Source {index}",
            },
        }
        for index, hit in enumerate(hits, start=1)
    )

    return {
        "query": query.strip(),
        "answer": answer,
        "sources": sources,
    }


def _format_context(
    hits: list[ClauseSearchHit],
    *,
    selection: str,
) -> list[str]:
    blocks: list[str] = []
    selected_norm = _normalize(selection) if selection else ""
    if selection:
        blocks.append(f"[Selected]\n{selection.strip()}")
    for index, hit in enumerate(hits, start=1):
        category = hit.clause_category or "clause"
        body = hit.content.strip()
        if selected_norm and _normalize(body) == selected_norm:
            continue
        blocks.append(f"[Source {index}] ({category})\n{body}")
    return blocks


def _normalize(text: str) -> str:
    return " ".join(text.split()).casefold()


def _store_turn(document_id: uuid.UUID, *, query: str, answer: str) -> None:
    with get_sync_db_session() as db:
        if document_crud.get(db, str(document_id)) is None:
            return
        document_message_crud.create(
            db,
            CreateDocumentMessage(
                document_id=document_id,
                role="user",
                content=query,
            ),
        )
        document_message_crud.create(
            db,
            CreateDocumentMessage(
                document_id=document_id,
                role="assistant",
                content=answer,
            ),
        )
