"""add_run_id_to_analysis_run

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-03 14:00:00.000000+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(
        "analysis_runs",
        sa.Column("run_id", sa.String(), nullable=True),
    )
    op.create_index(op.f("ix_analysis_runs_run_id"), "analysis_runs", ["run_id"], unique=False)
    if bind.dialect.name == "postgresql":
        op.create_foreign_key(
            "fk_analysis_runs_run_id_research_runs",
            "analysis_runs",
            "research_runs",
            ["run_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_constraint("fk_analysis_runs_run_id_research_runs", "analysis_runs", type_="foreignkey")
    op.drop_index(op.f("ix_analysis_runs_run_id"), table_name="analysis_runs")
    op.drop_column("analysis_runs", "run_id")