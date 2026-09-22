import html

from core.ast.parsers.ast import ASTNode

_HEADING_TAGS = {
    "section": "h1",
    "heading": "h2",
}


def node_to_html(node: ASTNode | dict) -> str:
    data = node.to_dict() if isinstance(node, ASTNode) else node
    node_type = data.get("node_type") or "paragraph"
    if node_type == "image":
        return _image_html(data)
    if node_type == "table":
        return _table_html(data)
    if node_type in {"table_header", "table_row", "table_cell"}:
        return ""

    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    parts: list[str] = []
    heading_tag = _HEADING_TAGS.get(node_type)
    if heading_tag and title:
        parts.append(f"<{heading_tag}>{html.escape(title)}</{heading_tag}>")
        if content:
            parts.append(f"<p>{html.escape(content)}</p>")
    elif title and content:
        parts.append(
            f"<p><strong>{html.escape(title)}</strong> {html.escape(content)}</p>"
        )
    elif title:
        parts.append(f"<p><strong>{html.escape(title)}</strong></p>")
    elif content:
        parts.append(f"<p>{html.escape(content)}</p>")

    for child in data.get("children") or []:
        parts.append(node_to_html(child))
    return "".join(parts)


def _image_html(data: dict) -> str:
    metadata = data.get("metadata") or {}
    src = metadata.get("src")
    if not isinstance(src, str) or not src.strip():
        return ""
    return f'<p><img src="{html.escape(src, quote=True)}" alt=""></p>'


def _table_html(data: dict) -> str:
    rows: list[str] = []
    for row in data.get("children") or []:
        row_data = row.to_dict() if isinstance(row, ASTNode) else row
        tag = "th" if row_data.get("node_type") == "table_header" else "td"
        cells: list[str] = []
        for cell in row_data.get("children") or []:
            cell_data = cell.to_dict() if isinstance(cell, ASTNode) else cell
            text = html.escape((cell_data.get("content") or "").strip())
            cells.append(f"<{tag}>{text}</{tag}>")
        if not cells and row_data.get("content"):
            cells.append(f"<{tag}>{html.escape(row_data['content'])}</{tag}>")
        if cells:
            rows.append(f"<tr>{''.join(cells)}</tr>")
    if not rows:
        return ""
    return f"<table><tbody>{''.join(rows)}</tbody></table>"
