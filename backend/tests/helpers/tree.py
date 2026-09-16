from core.ast.parsers.ast import ASTNode


def walk(nodes: list[ASTNode]):
    for node in nodes:
        yield node
        yield from walk(node.children)


def by_title(nodes: list[ASTNode], title: str) -> list[ASTNode]:
    return [node for node in walk(nodes) if node.title == title]


def by_type(nodes: list[ASTNode], node_type: str) -> list[ASTNode]:
    return [node for node in walk(nodes) if node.node_type == node_type]


def first_title(nodes: list[ASTNode], title: str) -> ASTNode:
    matches = by_title(nodes, title)
    if not matches:
        raise AssertionError(f"No AST node titled {title!r}")
    return matches[0]
