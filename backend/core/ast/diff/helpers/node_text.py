from core.ast.parsers.ast import ASTNode

from .view_node import view_node


def node_text(node: ASTNode | dict) -> str:
    viewed = view_node(node)
    return " ".join(part for part in (viewed.title, viewed.content) if part)
