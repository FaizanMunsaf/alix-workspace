import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from core.models.documents import Document


class DocumentChange(Base):
    __tablename__ = "document_changes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    result_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    actor: Mapped[str] = mapped_column(String(20), nullable=False)
    instruction: Mapped[str | None] = mapped_column(Text, nullable=True)
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    before_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    after_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    document: Mapped["Document"] = relationship(back_populates="changes")

    @property
    def before(self) -> str:
        return self.before_text

    @property
    def after(self) -> str:
        return self.after_text
