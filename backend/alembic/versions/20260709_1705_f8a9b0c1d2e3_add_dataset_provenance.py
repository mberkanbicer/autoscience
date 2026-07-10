"""Add dataset provenance columns (uploaded_by, original_filename, provenance)

Revision ID: f8a9b0c1d2e3
Revises: f7a8b9c0d1e2
Create Date: 2026-07-09 17:05:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f8a9b0c1d2e3"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "datasets",
        sa.Column("uploaded_by", sa.String(255), nullable=True),
    )
    op.add_column(
        "datasets",
        sa.Column("original_filename", sa.String(500), nullable=True),
    )
    op.add_column(
        "datasets",
        sa.Column("provenance", sa.String(50), nullable=True),
    )


def downgrade():
    op.drop_column("datasets", "provenance")
    op.drop_column("datasets", "original_filename")
    op.drop_column("datasets", "uploaded_by")
