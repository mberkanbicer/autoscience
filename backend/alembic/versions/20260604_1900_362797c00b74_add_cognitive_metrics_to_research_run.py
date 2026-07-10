"""add_cognitive_metrics_to_research_run

Revision ID: 362797c00b74
Revises: 002_add_cascade_deletes
Create Date: 2026-06-04 19:00:21.184589+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '362797c00b74'
down_revision: Union[str, None] = '002_add_cascade_deletes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add cognitive health metrics to research_runs
    op.add_column('research_runs', sa.Column('cognitive_entropy', sa.Float(), nullable=True))
    op.add_column('research_runs', sa.Column('cognitive_mode', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('research_runs', 'cognitive_mode')
    op.drop_column('research_runs', 'cognitive_entropy')
