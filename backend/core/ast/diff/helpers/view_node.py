from dataclasses import dataclass

from core.ast.parsers.ast import ASTNode


@dataclass(frozen=True)
class NodeView:
    node_type: str
    title: str | None
    content: str | None
    metadata: dict
    children: list


def view_node(node: ASTNode | dict) -> NodeView:
    if isinstance(node, ASTNode):
        return NodeView(
            node_type=node.node_type,
            title=node.title,
            content=node.content,
            metadata=node.metadata or {},
            children=node.children,
        )
    return NodeView(
        node_type=node.get("node_type") or "",
        title=node.get("title"),
        content=node.get("content"),
        metadata=node.get("metadata") or {},
        children=node.get("children") or [],
    )
