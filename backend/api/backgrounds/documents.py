import logging
import uuid
from pathlib import Path

from fastapi import BackgroundTasks
from langchain_core.documents import Document as LangchainDocument

from core.database import get_sync_db_session
from core.parsers import ASTNode, parse_docx
from core.repositories import (
    document_ast_node_crud,
    document_crud,
    document_version_crud,
)
from core.schemas.document import UpdateDocument
from core.schemas.document_ast_node import CreateDocumentASTNode
from core.schemas.document_version import UpdateDocumentVersion
from ds.rag.vectorstores import get_vectorstore

logger = logging.getLogger(__name__)


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
        ast_rows, vector_docs = _flatten_ast(
            tree,
            version_id=version_uuid,
            document_id=document_id,
            title=title,
            filename=filename,
        )

        with get_sync_db_session() as db:
            document = document_crud.get(db, document_id)
            version = document_version_crud.get(db, version_id)
            if document is None or version is None:
                logger.error("Document or version missing after parse: %s", document_id)
                return
            if ast_rows:
                document_ast_node_crud.create_many(db, ast_rows)
            document_crud.update(db, document_id, UpdateDocument(status="ingested"))
            document_version_crud.update(
                db,
                version_id,
                UpdateDocumentVersion(
                    raw_text=raw_text,
                    ast_json={"nodes": [node.to_dict() for node in tree]},
                    processing_status="completed",
                ),
            )

        if vector_docs:
            get_vectorstore().store(vector_docs)
        logger.info("Parsed document %s into %s AST nodes", document_id, len(ast_rows))
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
    document_id: str,
    title: str,
    filename: str,
    parent_id: uuid.UUID | None = None,
) -> tuple[list[CreateDocumentASTNode], list[LangchainDocument]]:
    rows: list[CreateDocumentASTNode] = []
    docs: list[LangchainDocument] = []
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
        page_content = "\n".join(
            part for part in (node.title, node.content) if part and part.strip()
        )
        if page_content:
            docs.append(
                LangchainDocument(
                    page_content=page_content,
                    metadata={
                        "document_id": document_id,
                        "version_id": str(version_id),
                        "ast_node_id": str(node_id),
                        "node_type": node.node_type,
                        "title": title,
                        "filename": filename,
                    },
                )
            )
        child_rows, child_docs = _flatten_ast(
            node.children,
            version_id=version_id,
            document_id=document_id,
            title=title,
            filename=filename,
            parent_id=node_id,
        )
        rows.extend(child_rows)
        docs.extend(child_docs)
    return rows, docs
