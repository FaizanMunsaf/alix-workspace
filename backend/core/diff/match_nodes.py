from core.parsers.ast import ASTNode
from core.utils.diff.node_identity import node_identity
from core.utils.diff.node_text import node_text
from core.utils.diff.similarity import similarity
from core.utils.diff.view_node import view_node

_FUZZY_THRESHOLD = 0.55


def match_nodes(
    old_nodes: list[ASTNode | dict],
    new_nodes: list[ASTNode | dict],
) -> tuple[list[tuple[ASTNode | dict, ASTNode | dict]], list, list]:
    paired_old: set[int] = set()
    paired_new: set[int] = set()
    pairs: list[tuple[ASTNode | dict, ASTNode | dict]] = []

    old_by_key: dict[str, list[int]] = {}
    new_by_key: dict[str, list[int]] = {}
    for index, node in enumerate(old_nodes):
        old_by_key.setdefault(node_identity(node), []).append(index)
    for index, node in enumerate(new_nodes):
        new_by_key.setdefault(node_identity(node), []).append(index)

    for key, old_indexes in old_by_key.items():
        for old_index, new_index in zip(old_indexes, new_by_key.get(key, [])):
            pairs.append((old_nodes[old_index], new_nodes[new_index]))
            paired_old.add(old_index)
            paired_new.add(new_index)

    unmatched_old = [node for i, node in enumerate(old_nodes) if i not in paired_old]
    unmatched_new = [node for i, node in enumerate(new_nodes) if i not in paired_new]
    used_new: set[int] = set()
    still_old: list[ASTNode | dict] = []

    for old_node in unmatched_old:
        best_index = None
        best_score = _FUZZY_THRESHOLD
        old_type = view_node(old_node).node_type
        for index, new_node in enumerate(unmatched_new):
            if index in used_new or view_node(new_node).node_type != old_type:
                continue
            score = similarity(node_text(old_node), node_text(new_node))
            if score > best_score:
                best_score = score
                best_index = index
        if best_index is None:
            still_old.append(old_node)
            continue
        pairs.append((old_node, unmatched_new[best_index]))
        used_new.add(best_index)

    still_new = [node for i, node in enumerate(unmatched_new) if i not in used_new]
    return pairs, still_old, still_new
