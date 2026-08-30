import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from core.models.clause_embeddings import ClauseEmbedding
    from core.models.document_version import DocumentVersion


class DocumentASTNode(Base):
    __tablename__ = "document_ast_nodes"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Foreign keys
    version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Columns
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("document_ast_nodes.id", ondelete="CASCADE"),
        nullable=True,
    )
    node_type: Mapped[str] = mapped_column(String(50), nullable=False)
    node_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_info: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    version: Mapped["DocumentVersion"] = relationship(back_populates="ast_nodes")
    parent: Mapped[Optional["DocumentASTNode"]] = relationship(
        "DocumentASTNode",
        back_populates="children",
        remote_side="DocumentASTNode.id",
    )
    children: Mapped[List["DocumentASTNode"]] = relationship(
        "DocumentASTNode",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    embeddings: Mapped[List["ClauseEmbedding"]] = relationship(
        back_populates="ast_node",
        cascade="all, delete-orphan",
    )
