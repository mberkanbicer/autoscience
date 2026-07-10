"""add_review_proposals

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    op.create_table(
        "review_proposals",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("created_by_id", sa.String(), nullable=False),
        sa.Column("assignee_id", sa.String(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_proposals_project_id", "review_proposals", ["project_id"])
    op.create_index("ix_review_proposals_status", "review_proposals", ["status"])
    op.create_index("ix_review_proposals_entity_type", "review_proposals", ["entity_type"])
    if bind.dialect.name == "postgresql":
        op.create_foreign_key(
            "fk_review_proposals_assignee_id_users",
            "review_proposals",
            "users",
            ["assignee_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_constraint("fk_review_proposals_assignee_id_users", "review_proposals", type_="foreignkey")
    op.drop_index("ix_review_proposals_entity_type", table_name="review_proposals")
    op.drop_index("ix_review_proposals_status", table_name="review_proposals")
    op.drop_index("ix_review_proposals_project_id", table_name="review_proposals")
    op.drop_table("review_proposals")