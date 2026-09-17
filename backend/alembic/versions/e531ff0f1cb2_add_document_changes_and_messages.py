"""add document changes and messages

Revision ID: e531ff0f1cb2
Revises: c4a91e2b7d06
Create Date: 2026-09-17 16:47:29.168232

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e531ff0f1cb2"
down_revision: Union[str, Sequence[str], None] = "c4a91e2b7d06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "document_changes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("version_id", sa.UUID(), nullable=True),
        sa.Column("result_version_id", sa.UUID(), nullable=True),
        sa.Column("actor", sa.String(length=20), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=True),
        sa.Column("target", sa.String(length=255), nullable=False),
        sa.Column(
            "before_text",
            sa.Text(),
            nullable=False,
            server_default=sa.text("''"),
        ),
        sa.Column(
            "after_text",
            sa.Text(),
            nullable=False,
            server_default=sa.text("''"),
        ),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column(
            "decision",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "document_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("document_messages")
    op.drop_table("document_changes")
