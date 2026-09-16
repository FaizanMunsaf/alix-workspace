from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ASTNode:
    node_type: str
    level: int
    title: str | None = None
    content: str | None = None
    metadata: dict = field(default_factory=dict)
    children: list[ASTNode] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "node_type": self.node_type,
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata,
            "children": [child.to_dict() for child in self.children],
        }
