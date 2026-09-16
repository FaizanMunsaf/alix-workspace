from core.ast.parsers.ast import ASTNode
from core.utils.export.node_to_html import node_to_html


def ast_to_html(nodes: list[ASTNode] | list[dict] | None) -> str:
    if not nodes:
        return "<p></p>"
    html = "".join(node_to_html(node) for node in nodes)
    return html or "<p></p>"
