from core.ast.parsers.ast import ASTNode


def normalize_tree(tree: list | dict | ASTNode | None) -> list:
    if tree is None:
        return []
    if isinstance(tree, ASTNode):
        return [tree]
    if isinstance(tree, dict):
        if "nodes" in tree:
            return list(tree["nodes"] or [])
        if tree.get("node_type"):
            return [tree]
        return []
    return list(tree)
