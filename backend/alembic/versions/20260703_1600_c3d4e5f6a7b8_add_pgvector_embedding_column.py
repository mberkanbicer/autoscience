"""add_pgvector_embedding_column

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-03 16:00:00.000000+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    # Check if the pgvector extension is available BEFORE attempting to create it.
    # CREATE EXTENSION inside a transaction aborts the entire transaction if the
    # extension isn't installed on the server, even when wrapped in try/except.
    result = bind.execute(
        sa.text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
    )
    if not result.fetchone():
        # pgvector not installed on this server — skip vector column
        return

    try:
        from pgvector.sqlalchemy import Vector
    except ImportError:
        return

    op.add_column(
        "paper_embeddings",
        sa.Column("embedding_vector", Vector(1536), nullable=True),
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.drop_column("paper_embeddings", "embedding_vector")