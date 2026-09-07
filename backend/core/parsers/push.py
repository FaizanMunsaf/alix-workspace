from core.parsers.ast import ASTNode


def push(stack: list[ASTNode], roots: list[ASTNode], node: ASTNode) -> None:
    while stack and stack[-1].level >= node.level:
        stack.pop()
    if stack:
        stack[-1].children.append(node)
    else:
        roots.append(node)
    stack.append(node)
