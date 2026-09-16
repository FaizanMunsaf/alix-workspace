from docx.table import Table

from .ast import ASTNode
from .helpers.truncate import truncate


def parse_table(table: Table, title: str | None = None) -> ASTNode | None:
    if not table.rows:
        return None

    headers = [cell.text.strip() for cell in table.rows[0].cells]
    header_line = " | ".join(h for h in headers if h)
    row_nodes: list[ASTNode] = []
    row_summaries: list[str] = []

    for row_index, row in enumerate(table.rows):
        is_header = row_index == 0
        values = [cell.text.strip() for cell in row.cells]
        cell_nodes: list[ASTNode] = []
        pairs: list[str] = []

        for col_index, value in enumerate(values):
            header = headers[col_index] if col_index < len(headers) else None
            if header and value and not is_header:
                pairs.append(f"{header}: {value}")
            elif value:
                pairs.append(value)
            cell_nodes.append(
                ASTNode(
                    node_type="table_cell",
                    level=52,
                    title=truncate(header) if header and not is_header else None,
                    content=value or None,
                    metadata={
                        "source": "table",
                        "row_index": row_index,
                        "col_index": col_index,
                        "header": is_header,
                    },
                )
            )

        row_summary = " | ".join(pairs)
        if row_summary:
            row_summaries.append(row_summary)
        row_title = values[0] if not is_header and values and values[0] else header_line
        row_nodes.append(
            ASTNode(
                node_type="table_header" if is_header else "table_row",
                level=51,
                title=truncate(row_title) if row_title else None,
                content=row_summary or None,
                metadata={"source": "table", "row_index": row_index},
                children=cell_nodes,
            )
        )

    table_title = title or header_line or "Table"
    return ASTNode(
        node_type="table",
        level=50,
        title=truncate(table_title),
        content="\n".join(row_summaries) or None,
        metadata={
            "source": "table",
            "rows": len(table.rows),
            "cols": len(table.columns),
            "headers": headers,
        },
        children=row_nodes,
    )
