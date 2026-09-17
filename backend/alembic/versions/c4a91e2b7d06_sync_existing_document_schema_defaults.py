"""sync existing document schema defaults

Revision ID: c4a91e2b7d06
Revises: a53f18e075ac
Create Date: 2026-09-17 16:55:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c4a91e2b7d06"
down_revision: Union[str, Sequence[str], None] = "a53f18e075ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "documents",
        "status",
        existing_type=sa.String(length=50),
        existing_nullable=False,
        server_default=sa.text("'draft'"),
    )
    op.alter_column(
        "documents",
        "metadata",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
        server_default=sa.text("'{}'::jsonb"),
    )
    op.alter_column(
        "document_versions",
        "version_number",
        existing_type=sa.Integer(),
        existing_nullable=False,
        server_default=sa.text("1"),
    )
    op.alter_column(
        "document_versions",
        "processing_status",
        existing_type=sa.String(length=50),
        existing_nullable=False,
        server_default=sa.text("'pending'"),
    )
    op.alter_column(
        "document_ast_nodes",
        "metadata",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
        server_default=sa.text("'{}'::jsonb"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "document_ast_nodes",
        "metadata",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
        server_default=None,
    )
    op.alter_column(
        "document_versions",
        "processing_status",
        existing_type=sa.String(length=50),
        existing_nullable=False,
        server_default=None,
    )
    op.alter_column(
        "document_versions",
        "version_number",
        existing_type=sa.Integer(),
        existing_nullable=False,
        server_default=None,
    )
    op.alter_column(
        "documents",
        "metadata",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
        server_default=None,
    )
    op.alter_column(
        "documents",
        "status",
        existing_type=sa.String(length=50),
        existing_nullable=False,
        server_default=None,
    )
