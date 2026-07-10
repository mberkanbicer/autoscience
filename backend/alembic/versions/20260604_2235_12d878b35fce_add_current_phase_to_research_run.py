"""add_current_phase_to_research_run

Revision ID: 12d878b35fce
Revises: d7fd02f2bc42
Create Date: 2026-06-04 22:35:19.419485+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '12d878b35fce'
down_revision: Union[str, None] = 'd7fd02f2bc42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add current_phase to research_runs
    op.add_column('research_runs', sa.Column('current_phase', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('research_runs', 'current_phase')
