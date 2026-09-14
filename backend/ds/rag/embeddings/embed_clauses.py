from ds.rag.embeddings import get_embedding_model
from core.schemas.clause_embedding import ClauseEmbedInput, CreateClauseEmbedding

_BATCH_SIZE = 100


def embed_clauses(items: list[ClauseEmbedInput]) -> list[CreateClauseEmbedding]:
    if not items:
        return []

    model = get_embedding_model()
    vectors: list[list[float]] = []
    texts = [item.content for item in items]
    for start in range(0, len(texts), _BATCH_SIZE):
        vectors.extend(model.embed_documents(texts[start : start + _BATCH_SIZE]))

    return [
        CreateClauseEmbedding(
            version_id=item.version_id,
            ast_node_id=item.ast_node_id,
            clause_category=item.clause_category,
            content=item.content,
            embedding=vector,
        )
        for item, vector in zip(items, vectors)
    ]
