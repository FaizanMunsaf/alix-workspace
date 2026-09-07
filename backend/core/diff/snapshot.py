from core.parsers.ast import ASTNode
from core.utils.diff.view_node import view_node


def snapshot(node: ASTNode | dict) -> dict:
    viewed = view_node(node)
    return {
        "node_type": viewed.node_type,
        "title": viewed.title,
        "content": viewed.content,
        "metadata": viewed.metadata,
    }
