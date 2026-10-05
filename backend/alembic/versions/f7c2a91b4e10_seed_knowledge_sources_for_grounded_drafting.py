"""seed knowledge sources for grounded drafting

Revision ID: f7c2a91b4e10
Revises: e531ff0f1cb2
Create Date: 2026-10-02 18:45:00.000000

"""

from typing import Sequence, Union

import pgvector
import sqlalchemy as sa
from alembic import op

revision: str = "f7c2a91b4e10"
down_revision: Union[str, Sequence[str], None] = "e531ff0f1cb2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_layer", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_knowledge_sources_source_layer",
        "knowledge_sources",
        ["source_layer"],
    )
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "embedding",
            pgvector.sqlalchemy.vector.VECTOR(dim=3072),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["knowledge_sources.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_knowledge_chunks_source_id",
        "knowledge_chunks",
        ["source_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_chunks_source_id", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")
    op.drop_index("ix_knowledge_sources_source_layer", table_name="knowledge_sources")
    op.drop_table("knowledge_sources")
