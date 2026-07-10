"""add_run_id_to_clusters_and_conflicts

Revision ID: d7fd02f2bc42
Revises: 24fc296a2de1
Create Date: 2026-06-04 21:56:19.419485+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd7fd02f2bc42'
down_revision: Union[str, None] = '24fc296a2de1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column('cluster_conflicts', sa.Column('run_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_cluster_conflicts_run_id'), 'cluster_conflicts', ['run_id'], unique=False)
    if bind.dialect.name == "postgresql":
        op.create_foreign_key(
            "fk_cluster_conflicts_run_id_research_runs",
            'cluster_conflicts', 'research_runs', ['run_id'], ['id'], ondelete='SET NULL',
        )

    op.add_column('paper_clusters', sa.Column('run_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_paper_clusters_run_id'), 'paper_clusters', ['run_id'], unique=False)
    if bind.dialect.name == "postgresql":
        op.create_foreign_key(
            "fk_paper_clusters_run_id_research_runs",
            'paper_clusters', 'research_runs', ['run_id'], ['id'], ondelete='SET NULL',
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_constraint("fk_paper_clusters_run_id_research_runs", 'paper_clusters', type_='foreignkey')
    op.drop_index(op.f('ix_paper_clusters_run_id'), table_name='paper_clusters')
    op.drop_column('paper_clusters', 'run_id')

    if bind.dialect.name == "postgresql":
        op.drop_constraint("fk_cluster_conflicts_run_id_research_runs", 'cluster_conflicts', type_='foreignkey')
    op.drop_index(op.f('ix_cluster_conflicts_run_id'), table_name='cluster_conflicts')
    op.drop_column('cluster_conflicts', 'run_id')
