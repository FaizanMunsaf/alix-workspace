import uuid

from fastapi import HTTPException

from core.database import get_sync_db_session
from core.repositories import clause_embedding_crud
from ds.rag.embeddings import get_embedding_model
from ds.rag.llms import get_llm


def answer_question(*, query: str, document_id: str | None, top_k: int) -> dict:
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

    query_embedding = get_embedding_model().embed_query(query.strip())
    with get_sync_db_session() as db:
        hits = clause_embedding_crud.search(
            db,
            query_embedding,
            top_k=top_k,
            document_id=document_uuid,
        )
    answer = get_llm().generate(query, [hit.content for hit in hits])

    return {
        "query": query,
        "answer": answer,
        "sources": [
            {
                "content": hit.content,
                "metadata": {
                    "document_id": str(hit.document_id),
                    "version_id": str(hit.version_id),
                    "ast_node_id": str(hit.ast_node_id),
                    "clause_category": hit.clause_category,
                    "distance": hit.distance,
                },
            }
            for hit in hits
        ],
    }
