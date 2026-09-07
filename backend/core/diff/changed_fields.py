from core.utils.diff.view_node import NodeView


def changed_fields(old: NodeView, new: NodeView) -> list[str]:
    fields: list[str] = []
    if old.node_type != new.node_type:
        fields.append("node_type")
    if (old.title or "") != (new.title or ""):
        fields.append("title")
    if (old.content or "") != (new.content or ""):
        fields.append("content")
    return fields
