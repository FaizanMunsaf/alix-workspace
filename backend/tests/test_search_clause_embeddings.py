import uuid

from sqlalchemy.dialects import postgresql

from core.ast.parsers.ast import ASTNode
from core.repositories.clause_embedding import clause_embedding_crud
from api.backgrounds.documents import _clause_embed_input


# this function use for check search sql use <=> on clause_embeddings
def test_search_query_uses_pgvector_cosine_operator():
    query = [0.1, 0.2, 0.3]
    document_id = uuid.uuid4()
    stmt = clause_embedding_crud.search_query(query, top_k=5, document_id=document_id)
    compiled = str(stmt.compile(dialect=postgresql.dialect()))

    assert "<=>" in compiled
    assert "clause_embeddings" in compiled
    assert "document_versions" in compiled
    assert "LIMIT" in compiled.upper()


# this function use for check empty nodes and table cells are not embedded
def test_clause_embed_input_skips_table_cells_and_empty_nodes():
    version_id = uuid.uuid4()
    clause = ASTNode(
        node_type="clause",
        level=10,
        title="1.1",
        content="Confidential Information means non-public data.",
    )
    cell = ASTNode(node_type="table_cell", level=52, content="USD")
    empty = ASTNode(node_type="heading", level=1, title=None, content=None)

    kept = _clause_embed_input(clause, node_id=uuid.uuid4(), version_id=version_id)
    skipped_cell = _clause_embed_input(
        cell, node_id=uuid.uuid4(), version_id=version_id
    )
    skipped_empty = _clause_embed_input(
        empty, node_id=uuid.uuid4(), version_id=version_id
    )

    assert kept is not None
    assert kept.clause_category == "clause"
    assert "Confidential Information" in kept.content
    assert skipped_cell is None
    assert skipped_empty is None
