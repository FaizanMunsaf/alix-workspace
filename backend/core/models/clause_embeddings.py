import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.config.settings import settings
from core.database import Base

if TYPE_CHECKING:
    from core.models.document_ast_node import DocumentASTNode
    from core.models.document_version import DocumentVersion


class ClauseEmbedding(Base):
    __tablename__ = "clause_embeddings"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Foreign keys
    version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    ast_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_ast_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Columns
    clause_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Vector] = mapped_column(
        Vector(settings.EMBEDDING_DIMENSION), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    version: Mapped["DocumentVersion"] = relationship(back_populates="embeddings")
    ast_node: Mapped["DocumentASTNode"] = relationship(back_populates="embeddings")
