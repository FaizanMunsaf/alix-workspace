from core.ast.parsers.ast import ASTNode

from .view_node import view_node


def node_identity(node: ASTNode | dict) -> str:
    viewed = view_node(node)
    number = viewed.metadata.get("number")
    if number is not None and str(number).strip():
        return f"{viewed.node_type}:num:{_norm(str(number))}"

    if viewed.node_type == "table_cell":
        col_index = viewed.metadata.get("col_index")
        if col_index is not None:
            return f"table_cell:{col_index}"

    if viewed.node_type in {"table_row", "table_header"} and viewed.title:
        return f"{viewed.node_type}:title:{_norm(viewed.title)}"

    if viewed.title:
        return f"{viewed.node_type}:title:{_norm(viewed.title)}"
    if viewed.content:
        return f"{viewed.node_type}:content:{_norm(viewed.content)}"
    return f"{viewed.node_type}:empty"


def _norm(value: str) -> str:
    return " ".join(value.lower().split())
