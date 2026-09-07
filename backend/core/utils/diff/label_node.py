from core.utils.diff.view_node import NodeView
from core.utils.parsers.truncate import truncate


def label_node(viewed: NodeView) -> str:
    if viewed.title:
        return viewed.title
    if viewed.content:
        return truncate(" ".join(viewed.content.split()), 60)
    return viewed.node_type or "node"
