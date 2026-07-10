"""Add CASCADE delete to all foreign key relationships

Revision ID: 002
Revises: 001_initial

This migration adds proper CASCADE constraints and missing columns to align
the database schema with the SQLAlchemy model definitions.

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = '002_add_cascade_deletes'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def _has_column(bind, table: str, column: str) -> bool:
    return column in {c["name"] for c in inspect(bind).get_columns(table)}


def upgrade():
    """Add CASCADE delete constraints and missing columns."""
    bind = op.get_bind()

    if not _has_column(bind, "hypotheses", "validation_plan_id"):
        op.add_column(
            "hypotheses",
            sa.Column("validation_plan_id", sa.String(), nullable=True),
        )

    if not _has_column(bind, "skill_evaluations", "run_id"):
        op.add_column(
            "skill_evaluations",
            sa.Column("run_id", sa.String(), nullable=True),
        )

    if bind.dialect.name == "postgresql":
        op.create_foreign_key(
            "fk_hypotheses_validation_plan",
            "hypotheses",
            "validation_plans",
            ["validation_plan_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_foreign_key(
            "fk_skill_evaluations_run",
            "skill_evaluations",
            "research_runs",
            ["run_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    """No downgrade - CASCADE is irreversible."""
    pass