from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ChangeStatus = Literal["added", "deleted", "modified"]


@dataclass
class DiffChange:
    status: ChangeStatus
    path: str
    node_type: str
    title: str | None = None
    fields: list[str] = field(default_factory=list)
    before: dict | None = None
    after: dict | None = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "path": self.path,
            "node_type": self.node_type,
            "title": self.title,
            "fields": self.fields,
            "before": self.before,
            "after": self.after,
        }


@dataclass
class ASTDiff:
    added: list[DiffChange] = field(default_factory=list)
    deleted: list[DiffChange] = field(default_factory=list)
    modified: list[DiffChange] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "added": [change.to_dict() for change in self.added],
            "deleted": [change.to_dict() for change in self.deleted],
            "modified": [change.to_dict() for change in self.modified],
            "summary": {
                "added": len(self.added),
                "deleted": len(self.deleted),
                "modified": len(self.modified),
            },
        }
