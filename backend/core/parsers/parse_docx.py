import logging
from io import BytesIO

from docx import Document as DocxDocument
from docx.table import Table

from core.parsers.ast import ASTNode
from core.parsers.classify_paragraph import classify_paragraph
from core.parsers.parse_table import parse_table
from core.parsers.push import push
from core.utils.parsers.iter_blocks import iter_blocks

logger = logging.getLogger(__name__)


def parse_docx(data: bytes) -> tuple[str, list[ASTNode]]:
    document = DocxDocument(BytesIO(data))
    roots: list[ASTNode] = []
    stack: list[ASTNode] = []
    raw_parts: list[str] = []

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
        if not text:
            continue
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
            continue
        push(stack, roots, classified)

    raw_text = "\n".join(raw_parts)
    logger.info("Parsed docx into %s top-level AST nodes", len(roots))
    return raw_text, roots
