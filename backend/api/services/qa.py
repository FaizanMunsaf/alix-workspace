from fastapi import HTTPException

from ds.rag.llms import get_llm
from ds.rag.vectorstores import get_vectorstore


def answer_question(*, query: str, document_id: str | None, top_k: int) -> dict:
    if not query.strip():
        raise HTTPException(status_code=400, detail="query is required.")

    metadata_filter = {"document_id": document_id} if document_id else None
    context = get_vectorstore().search(query, top_k=top_k, filter=metadata_filter)
    answer = get_llm().generate(query, context)

    return {
        "query": query,
        "answer": answer,
        "sources": [
            {"content": doc.page_content, "metadata": doc.metadata} for doc in context
        ],
    }
