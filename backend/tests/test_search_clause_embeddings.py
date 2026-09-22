import uuid

from sqlalchemy.dialects import postgresql

from api.backgrounds.documents import _clause_embed_input, _flatten_ast
from core.ast.parsers.ast import ASTNode
from core.repositories.clause_embedding import clause_embedding_crud


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
    assert "version_number" in compiled


def test_search_query_can_pin_explicit_version():
    query = [0.1, 0.2, 0.3]
    version_id = uuid.uuid4()
    stmt = clause_embedding_crud.search_query(query, top_k=5, version_id=version_id)
    compiled = str(stmt.compile(dialect=postgresql.dialect()))
    assert "version_id" in compiled


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
    image = ASTNode(
        node_type="image",
        level=55,
        metadata={"src": "data:image/png;base64,abc"},
    )

    kept = _clause_embed_input(clause, node_id=uuid.uuid4(), version_id=version_id)
    skipped_cell = _clause_embed_input(
        cell, node_id=uuid.uuid4(), version_id=version_id
    )
    skipped_empty = _clause_embed_input(
        empty, node_id=uuid.uuid4(), version_id=version_id
    )
    skipped_image = _clause_embed_input(
        image, node_id=uuid.uuid4(), version_id=version_id
    )

    assert kept is not None
    assert kept.clause_category == "clause"
    assert "Confidential Information" in kept.content
    assert skipped_cell is None
    assert skipped_empty is None
    assert skipped_image is None


def test_flatten_ast_builds_embed_inputs_for_version():
    version_id = uuid.uuid4()
    tree = [
        ASTNode(
            node_type="clause",
            level=10,
            title="2.1",
            content="The liability cap is 12 months of fees.",
        )
    ]
    rows, embeds = _flatten_ast(tree, version_id=version_id)
    assert len(rows) == 1
    assert len(embeds) == 1
    assert embeds[0].version_id == version_id
    assert embeds[0].ast_node_id == rows[0].id
    assert "liability cap" in embeds[0].content
