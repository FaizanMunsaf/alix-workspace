from core.diff.changed_fields import changed_fields
from core.diff.match_nodes import match_nodes
from core.diff.snapshot import snapshot
from core.diff.types import ASTDiff, ChangeStatus, DiffChange
from core.parsers.ast import ASTNode
from core.utils.diff.format_path import format_path
from core.utils.diff.label_node import label_node
from core.utils.diff.normalize_tree import normalize_tree
from core.utils.diff.view_node import view_node


def diff_ast(
    old_tree: list | dict | ASTNode | None, new_tree: list | dict | ASTNode | None
) -> ASTDiff:
    result = ASTDiff()
    _walk(normalize_tree(old_tree), normalize_tree(new_tree), [], result)
    return result


def _walk(
    old_nodes: list,
    new_nodes: list,
    path: list[str],
    result: ASTDiff,
) -> None:
    pairs, deleted, added = match_nodes(old_nodes, new_nodes)

    for node in deleted:
        _emit_subtree(node, path, result, "deleted")

    for node in added:
        _emit_subtree(node, path, result, "added")

    for old_node, new_node in pairs:
        old_view = view_node(old_node)
        new_view = view_node(new_node)
        fields = changed_fields(old_view, new_view)
        node_path = [*path, label_node(new_view) or label_node(old_view)]
        if fields:
            result.modified.append(
                DiffChange(
                    status="modified",
                    path=format_path(node_path),
                    node_type=new_view.node_type or old_view.node_type,
                    title=new_view.title or old_view.title,
                    fields=fields,
                    before=snapshot(old_node),
                    after=snapshot(new_node),
                )
            )
        _walk(old_view.children, new_view.children, node_path, result)


def _emit_subtree(node, path: list[str], result: ASTDiff, status: ChangeStatus) -> None:
    viewed = view_node(node)
    node_path = [*path, label_node(viewed)]
    change = DiffChange(
        status=status,
        path=format_path(node_path),
        node_type=viewed.node_type,
        title=viewed.title,
        before=snapshot(node) if status == "deleted" else None,
        after=snapshot(node) if status == "added" else None,
    )
    if status == "added":
        result.added.append(change)
    else:
        result.deleted.append(change)
    for child in viewed.children:
        _emit_subtree(child, node_path, result, status)
