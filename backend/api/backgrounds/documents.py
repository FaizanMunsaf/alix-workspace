import logging
import uuid
from pathlib import Path

from fastapi import BackgroundTasks

from core.database import get_sync_db_session
from core.ast.parsers import ASTNode, parse_docx
from core.repositories import (
    clause_embedding_crud,
    document_ast_node_crud,
    document_crud,
    document_version_crud,
)
from core.schemas.clause_embedding import ClauseEmbedInput
from core.schemas.document import UpdateDocument
from core.schemas.document_ast_node import CreateDocumentASTNode
from core.schemas.document_version import UpdateDocumentVersion
from core.utils.export import ast_to_html
from ds.rag.embeddings.embed_clauses import embed_clauses

logger = logging.getLogger(__name__)

_SKIP_EMBED_TYPES = {"table_cell"}


def enqueue_document_parse(
    background_tasks: BackgroundTasks,
    *,
    document_id: str,
    version_id: str,
    file_path: str,
    title: str,
    filename: str,
) -> None:
    background_tasks.add_task(
        parse_and_ingest_document,
        document_id,
        version_id,
        file_path,
        title,
        filename,
    )


def parse_and_ingest_document(
    document_id: str,
    version_id: str,
    file_path: str,
    title: str,
    filename: str,
) -> None:
    try:
        _set_processing_status(document_id, version_id, "processing", "processing")
        raw_text, tree = parse_docx(Path(file_path).read_bytes())
        if not raw_text.strip():
            raise ValueError("No text could be extracted from the .docx file.")

        version_uuid = uuid.UUID(version_id)
        ast_rows, embed_inputs = _flatten_ast(tree, version_id=version_uuid)

        with get_sync_db_session() as db:
            document = document_crud.get(db, document_id)
            version = document_version_crud.get(db, version_id)
            if document is None or version is None:
                logger.error("Document or version missing after parse: %s", document_id)
                return
            if ast_rows:
                document_ast_node_crud.create_many(db, ast_rows)
            document_version_crud.update(
                db,
                version_id,
                UpdateDocumentVersion(
                    raw_text=raw_text,
                    ast_json={
                        "nodes": [node.to_dict() for node in tree],
                        "html": ast_to_html(tree),
                    },
                ),
            )

        clause_rows = embed_clauses(embed_inputs)

        with get_sync_db_session() as db:
            if clause_rows:
                clause_embedding_crud.create_many(db, clause_rows)
            document_crud.update(db, document_id, UpdateDocument(status="ingested"))
            document_version_crud.update(
                db,
                version_id,
                UpdateDocumentVersion(processing_status="completed"),
            )

        logger.info(
            "Parsed document %s (%s) into %s AST nodes and %s clause embeddings",
            document_id,
            filename or title,
            len(ast_rows),
            len(clause_rows),
        )
    except Exception:
        logger.exception("Failed to parse document %s", document_id)
        _set_processing_status(document_id, version_id, "failed", "failed")


def _set_processing_status(
    document_id: str,
    version_id: str,
    document_status: str,
    version_status: str,
) -> None:
    with get_sync_db_session() as db:
        document_crud.update(db, document_id, UpdateDocument(status=document_status))
        document_version_crud.update(
            db, version_id, UpdateDocumentVersion(processing_status=version_status)
        )


def _flatten_ast(
    nodes: list[ASTNode],
    *,
    version_id: uuid.UUID,
    parent_id: uuid.UUID | None = None,
) -> tuple[list[CreateDocumentASTNode], list[ClauseEmbedInput]]:
    rows: list[CreateDocumentASTNode] = []
    embed_inputs: list[ClauseEmbedInput] = []
    for index, node in enumerate(nodes):
        node_id = uuid.uuid4()
        rows.append(
            CreateDocumentASTNode(
                id=node_id,
                version_id=version_id,
                parent_id=parent_id,
                node_type=node.node_type,
                node_index=index,
                title=node.title,
                content=node.content,
                metadata_info=node.metadata,
            )
        )
        embed_input = _clause_embed_input(node, node_id=node_id, version_id=version_id)
        if embed_input is not None:
            embed_inputs.append(embed_input)
        child_rows, child_embeds = _flatten_ast(
            node.children,
            version_id=version_id,
            parent_id=node_id,
        )
        rows.extend(child_rows)
        embed_inputs.extend(child_embeds)
    return rows, embed_inputs


def _clause_embed_input(
    node: ASTNode,
    *,
    node_id: uuid.UUID,
    version_id: uuid.UUID,
) -> ClauseEmbedInput | None:
    if node.node_type in _SKIP_EMBED_TYPES:
        return None
    content = "\n".join(
        part for part in (node.title, node.content) if part and part.strip()
    )
    if not content:
        return None
    return ClauseEmbedInput(
        version_id=version_id,
        ast_node_id=node_id,
        clause_category=node.node_type,
        content=content,
    )
