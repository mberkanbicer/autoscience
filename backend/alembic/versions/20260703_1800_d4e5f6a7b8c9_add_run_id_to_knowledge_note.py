"""add_run_id_to_knowledge_note

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-03 18:00:00.000000+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column("knowledge_notes", sa.Column("run_id", sa.String(), nullable=True))
    op.create_index(op.f("ix_knowledge_notes_run_id"), "knowledge_notes", ["run_id"], unique=False)
    if bind.dialect.name == "postgresql":
        op.create_foreign_key(
            "fk_knowledge_notes_run_id_research_runs",
            "knowledge_notes",
            "research_runs",
            ["run_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_constraint("fk_knowledge_notes_run_id_research_runs", "knowledge_notes", type_="foreignkey")
    op.drop_index(op.f("ix_knowledge_notes_run_id"), table_name="knowledge_notes")
    op.drop_column("knowledge_notes", "run_id")