import logging
from io import BytesIO
from pathlib import Path

from docx import Document as DocxDocument
from docx.table import Table

from .ast import ASTNode
from .classify_paragraph import classify_paragraph
from .helpers.extract_images import iter_paragraph_images, store_document_image
from .helpers.iter_blocks import iter_blocks
from .parse_table import parse_table
from .push import push

logger = logging.getLogger(__name__)


def parse_docx(
    data: bytes,
    *,
    document_id: str | None = None,
    media_dir: Path | None = None,
) -> tuple[str, list[ASTNode]]:
    document = DocxDocument(BytesIO(data))
    roots: list[ASTNode] = []
    stack: list[ASTNode] = []
    raw_parts: list[str] = []
    persist_images = bool(document_id and media_dir)

    for block in iter_blocks(document):
        if isinstance(block, Table):
            parent_title = stack[-1].title if stack else None
            table_node = parse_table(block, title=parent_title)
            if table_node is None:
                continue
            if table_node.content:
                raw_parts.append(table_node.content)
            push(stack, roots, table_node)
            continue

        text = block.text.strip()
        images = iter_paragraph_images(block, document)
        if not text and not images:
            continue

        if text:
            raw_parts.append(text)
            classified = classify_paragraph(block, text)
            if classified is None:
                push(
                    stack,
                    roots,
                    ASTNode(
                        node_type="paragraph",
                        level=50,
                        content=text,
                        metadata={"source": "body"},
                    ),
                )
            else:
                push(stack, roots, classified)

        if not persist_images:
            continue
        for content_type, blob in images:
            metadata = store_document_image(
                document_id=document_id,  # type: ignore[arg-type]
                media_dir=media_dir,  # type: ignore[arg-type]
                content_type=content_type,
                blob=blob,
            )
            push(
                stack,
                roots,
                ASTNode(
                    node_type="image",
                    level=50,
                    metadata=metadata,
                ),
            )

    raw_text = "\n".join(raw_parts)
    logger.info("Parsed docx into %s top-level AST nodes", len(roots))
    return raw_text, roots
