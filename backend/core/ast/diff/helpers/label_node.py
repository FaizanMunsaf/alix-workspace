from core.ast.parsers.helpers.truncate import truncate

from .view_node import NodeView


def label_node(viewed: NodeView) -> str:
    if viewed.title:
        return viewed.title
    if viewed.content:
        return truncate(" ".join(viewed.content.split()), 60)
    return viewed.node_type or "node"
