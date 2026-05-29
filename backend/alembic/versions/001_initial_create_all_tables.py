"""Initial migration - create all tables

Revision ID: 001_initial
Revises:
Create Date: 2025-01-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Projects
    op.create_table(
        'projects',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('subject_scope', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('out_of_scope', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('default_flexibility', sa.Float(), nullable=True),
        sa.Column('idle_research_enabled', sa.Boolean(), nullable=True),
        sa.Column('idle_trigger_minutes', sa.Integer(), nullable=True),
        sa.Column('max_idle_cycles_per_day', sa.Integer(), nullable=True),
        sa.Column('max_sources_per_cycle', sa.Integer(), nullable=True),
        sa.Column('approval_required_for_external_actions', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_projects_id', 'projects', ['id'])

    # Ideas
    op.create_table(
        'ideas',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('origin', sa.String(length=50), nullable=False),
        sa.Column('initial_text', sa.Text(), nullable=False),
        sa.Column('current_text', sa.Text(), nullable=False),
        sa.Column('flexibility', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('classification', sa.String(length=50), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('classification_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ideas_id', 'ideas', ['id'])
    op.create_index('ix_ideas_project_id', 'ideas', ['project_id'])
    op.create_index('ix_ideas_status', 'ideas', ['status'])
    op.create_index('ix_ideas_classification', 'ideas', ['classification'])

    # Idea Versions
    op.create_table(
        'idea_versions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('idea_id', sa.String(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_idea_versions_id', 'idea_versions', ['id'])
    op.create_index('ix_idea_versions_idea_id', 'idea_versions', ['idea_id'])

    # Idea Scores
    op.create_table(
        'idea_scores',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('idea_id', sa.String(), nullable=False),
        sa.Column('novelty', sa.Float(), nullable=True),
        sa.Column('feasibility', sa.Float(), nullable=True),
        sa.Column('importance', sa.Float(), nullable=True),
        sa.Column('evidence_support', sa.Float(), nullable=True),
        sa.Column('validation_clarity', sa.Float(), nullable=True),
        sa.Column('differentiation', sa.Float(), nullable=True),
        sa.Column('data_availability', sa.Float(), nullable=True),
        sa.Column('skill_leverage', sa.Float(), nullable=True),
        sa.Column('user_alignment', sa.Float(), nullable=True),
        sa.Column('prior_art_risk', sa.Float(), nullable=True),
        sa.Column('safety_risk', sa.Float(), nullable=True),
        sa.Column('cost_risk', sa.Float(), nullable=True),
        sa.Column('overall_value', sa.Float(), nullable=True),
        sa.Column('scoring_rationale', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_idea_scores_id', 'idea_scores', ['id'])
    op.create_index('ix_idea_scores_idea_id', 'idea_scores', ['idea_id'])

    # Idea Classifications
    op.create_table(
        'idea_classifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('idea_id', sa.String(), nullable=False),
        sa.Column('classification', sa.String(length=50), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_idea_classifications_id', 'idea_classifications', ['id'])
    op.create_index('ix_idea_classifications_idea_id', 'idea_classifications', ['idea_id'])

    # Idea Decisions
    op.create_table(
        'idea_decisions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('idea_id', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=True),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_idea_decisions_id', 'idea_decisions', ['id'])
    op.create_index('ix_idea_decisions_idea_id', 'idea_decisions', ['idea_id'])
    op.create_index('ix_idea_decisions_run_id', 'idea_decisions', ['run_id'])

    # Research Runs
    op.create_table(
        'research_runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('idea_id', sa.String(), nullable=True),
        sa.Column('run_type', sa.String(length=50), nullable=False),
        sa.Column('state', sa.String(length=50), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_minutes', sa.Integer(), nullable=True),
        sa.Column('max_sources', sa.Integer(), nullable=True),
        sa.Column('max_cost_usd', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_research_runs_id', 'research_runs', ['id'])
    op.create_index('ix_research_runs_project_id', 'research_runs', ['project_id'])
    op.create_index('ix_research_runs_idea_id', 'research_runs', ['idea_id'])
    op.create_index('ix_research_runs_state', 'research_runs', ['state'])

    # Research Run Events
    op.create_table(
        'research_run_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('actor', sa.String(length=100), nullable=True),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_research_run_events_id', 'research_run_events', ['id'])
    op.create_index('ix_research_run_events_run_id', 'research_run_events', ['run_id'])

    # Tool Calls
    op.create_table(
        'tool_calls',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=False),
        sa.Column('agent_role', sa.String(length=100), nullable=True),
        sa.Column('tool_name', sa.String(length=255), nullable=False),
        sa.Column('input_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('output_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tool_calls_id', 'tool_calls', ['id'])
    op.create_index('ix_tool_calls_run_id', 'tool_calls', ['run_id'])

    # Idle Cycles
    op.create_table(
        'idle_cycles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=True),
        sa.Column('idle_mode', sa.String(length=50), nullable=True),
        sa.Column('trigger_reason', sa.Text(), nullable=True),
        sa.Column('ideas_generated', sa.Integer(), nullable=True),
        sa.Column('questions_generated', sa.Integer(), nullable=True),
        sa.Column('hypotheses_generated', sa.Integer(), nullable=True),
        sa.Column('skills_created', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_idle_cycles_id', 'idle_cycles', ['id'])
    op.create_index('ix_idle_cycles_project_id', 'idle_cycles', ['project_id'])
    op.create_index('ix_idle_cycles_run_id', 'idle_cycles', ['run_id'])

    # Papers
    op.create_table(
        'papers',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('authors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('doi', sa.String(length=255), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('venue', sa.String(length=500), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('citation_count', sa.Integer(), nullable=True),
        sa.Column('paper_type', sa.String(length=50), nullable=True),
        sa.Column('source_connector', sa.String(length=100), nullable=True),
        sa.Column('source_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_papers_id', 'papers', ['id'])
    op.create_index('ix_papers_project_id', 'papers', ['project_id'])
    op.create_index('ix_papers_year', 'papers', ['year'])
    op.create_index('ix_papers_doi', 'papers', ['doi'])

    # Paper Sources
    op.create_table(
        'paper_sources',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('paper_id', sa.String(), nullable=False),
        sa.Column('connector', sa.String(length=100), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('raw_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_paper_sources_id', 'paper_sources', ['id'])
    op.create_index('ix_paper_sources_paper_id', 'paper_sources', ['paper_id'])

    # Paper Fulltexts
    op.create_table(
        'paper_fulltexts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('paper_id', sa.String(), nullable=False),
        sa.Column('fulltext', sa.Text(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_paper_fulltexts_id', 'paper_fulltexts', ['id'])
    op.create_index('ix_paper_fulltexts_paper_id', 'paper_fulltexts', ['paper_id'])

    # Paper Embeddings
    op.create_table(
        'paper_embeddings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('paper_id', sa.String(), nullable=False),
        sa.Column('embedding', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_paper_embeddings_id', 'paper_embeddings', ['id'])
    op.create_index('ix_paper_embeddings_paper_id', 'paper_embeddings', ['paper_id'])

    # Paper Analyses
    op.create_table(
        'paper_analyses',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('paper_id', sa.String(), nullable=False),
        sa.Column('problem', sa.Text(), nullable=True),
        sa.Column('method', sa.Text(), nullable=True),
        sa.Column('dataset_sample', sa.Text(), nullable=True),
        sa.Column('metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('findings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('limitations', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('future_work', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('assumptions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('relation_to_idea', sa.Text(), nullable=True),
        sa.Column('key_claims', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_paper_analyses_id', 'paper_analyses', ['id'])
    op.create_index('ix_paper_analyses_paper_id', 'paper_analyses', ['paper_id'])

    # Paper Clusters
    op.create_table(
        'paper_clusters',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cluster_type', sa.String(length=50), nullable=True),
        sa.Column('paper_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('representative_paper_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_paper_clusters_id', 'paper_clusters', ['id'])
    op.create_index('ix_paper_clusters_project_id', 'paper_clusters', ['project_id'])

    # Cluster Labels
    op.create_table(
        'cluster_labels',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('cluster_id', sa.String(), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cluster_labels_id', 'cluster_labels', ['id'])
    op.create_index('ix_cluster_labels_cluster_id', 'cluster_labels', ['cluster_id'])

    # Cluster Conflicts
    op.create_table(
        'cluster_conflicts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('cluster_id', sa.String(), nullable=True),
        sa.Column('conflict_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('supporting_papers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('opposing_papers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('research_opportunity', sa.Text(), nullable=True),
        sa.Column('severity', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cluster_conflicts_id', 'cluster_conflicts', ['id'])
    op.create_index('ix_cluster_conflicts_project_id', 'cluster_conflicts', ['project_id'])
    op.create_index('ix_cluster_conflicts_cluster_id', 'cluster_conflicts', ['cluster_id'])

    # Research Questions
    op.create_table(
        'research_questions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('idea_id', sa.String(), nullable=True),
        sa.Column('run_id', sa.String(), nullable=True),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('source_conflicts', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('source_gaps', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('rank', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_research_questions_id', 'research_questions', ['id'])
    op.create_index('ix_research_questions_project_id', 'research_questions', ['project_id'])
    op.create_index('ix_research_questions_idea_id', 'research_questions', ['idea_id'])
    op.create_index('ix_research_questions_run_id', 'research_questions', ['run_id'])
    op.create_index('ix_research_questions_status', 'research_questions', ['status'])

    # Hypotheses
    op.create_table(
        'hypotheses',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('idea_id', sa.String(), nullable=True),
        sa.Column('question_id', sa.String(), nullable=True),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('independent_variable', sa.Text(), nullable=True),
        sa.Column('dependent_variable', sa.Text(), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('expected_direction', sa.Text(), nullable=True),
        sa.Column('baseline', sa.Text(), nullable=True),
        sa.Column('metric', sa.Text(), nullable=True),
        sa.Column('dataset_requirement', sa.Text(), nullable=True),
        sa.Column('failure_condition', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_hypotheses_id', 'hypotheses', ['id'])
    op.create_index('ix_hypotheses_project_id', 'hypotheses', ['project_id'])
    op.create_index('ix_hypotheses_idea_id', 'hypotheses', ['idea_id'])
    op.create_index('ix_hypotheses_question_id', 'hypotheses', ['question_id'])
    op.create_index('ix_hypotheses_status', 'hypotheses', ['status'])

    # Validation Plans
    op.create_table(
        'validation_plans',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('hypothesis_id', sa.String(), nullable=False),
        sa.Column('dataset_candidates', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('benchmark_candidates', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('baselines', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('experimental_design', sa.Text(), nullable=True),
        sa.Column('statistical_tests', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('simulation_option', sa.Text(), nullable=True),
        sa.Column('expected_artifacts', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('difficulty_estimate', sa.Float(), nullable=True),
        sa.Column('cost_estimate', sa.Float(), nullable=True),
        sa.Column('feasibility_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_validation_plans_id', 'validation_plans', ['id'])
    op.create_index('ix_validation_plans_hypothesis_id', 'validation_plans', ['hypothesis_id'])

    # Skills
    op.create_table(
        'skills',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('skill_type', sa.String(length=50), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('trigger_conditions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('inputs', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('procedure', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('outputs', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=True),
        sa.Column('times_used', sa.Integer(), nullable=True),
        sa.Column('successful_uses', sa.Integer(), nullable=True),
        sa.Column('average_score_improvement', sa.Float(), nullable=True),
        sa.Column('failure_cases', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('domains_where_it_works', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('domains_where_it_fails', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_skills_id', 'skills', ['id'])
    op.create_index('ix_skills_project_id', 'skills', ['project_id'])
    op.create_index('ix_skills_status', 'skills', ['status'])

    # Skill Versions
    op.create_table(
        'skill_versions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('skill_id', sa.String(), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('changes', sa.Text(), nullable=True),
        sa.Column('procedure', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_skill_versions_id', 'skill_versions', ['id'])
    op.create_index('ix_skill_versions_skill_id', 'skill_versions', ['skill_id'])

    # Skill Usages
    op.create_table(
        'skill_usages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('skill_id', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('score_before', sa.Float(), nullable=True),
        sa.Column('score_after', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_skill_usages_id', 'skill_usages', ['id'])
    op.create_index('ix_skill_usages_skill_id', 'skill_usages', ['skill_id'])
    op.create_index('ix_skill_usages_run_id', 'skill_usages', ['run_id'])

    # Skill Evaluations
    op.create_table(
        'skill_evaluations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('skill_id', sa.String(), nullable=False),
        sa.Column('evaluator', sa.String(length=100), nullable=False),
        sa.Column('rating', sa.Float(), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_skill_evaluations_id', 'skill_evaluations', ['id'])
    op.create_index('ix_skill_evaluations_skill_id', 'skill_evaluations', ['skill_id'])

    # Research Reports
    op.create_table(
        'research_reports',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=True),
        sa.Column('idea_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('content_markdown', sa.Text(), nullable=True),
        sa.Column('content_html', sa.Text(), nullable=True),
        sa.Column('report_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_research_reports_id', 'research_reports', ['id'])
    op.create_index('ix_research_reports_project_id', 'research_reports', ['project_id'])
    op.create_index('ix_research_reports_run_id', 'research_reports', ['run_id'])
    op.create_index('ix_research_reports_idea_id', 'research_reports', ['idea_id'])

    # Knowledge Notes
    op.create_table(
        'knowledge_notes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('note_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('embedding', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('linked_notes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_knowledge_notes_id', 'knowledge_notes', ['id'])
    op.create_index('ix_knowledge_notes_project_id', 'knowledge_notes', ['project_id'])

    # Literature Searches
    op.create_table(
        'literature_searches',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=True),
        sa.Column('idea_id', sa.String(), nullable=True),
        sa.Column('total_results', sa.Integer(), nullable=True),
        sa.Column('papers_selected', sa.Integer(), nullable=True),
        sa.Column('queries_used', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('connectors_used', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_literature_searches_id', 'literature_searches', ['id'])
    op.create_index('ix_literature_searches_project_id', 'literature_searches', ['project_id'])
    op.create_index('ix_literature_searches_run_id', 'literature_searches', ['run_id'])
    op.create_index('ix_literature_searches_idea_id', 'literature_searches', ['idea_id'])

    # Search Queries
    op.create_table(
        'search_queries',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('search_id', sa.String(), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('query_type', sa.String(length=50), nullable=True),
        sa.Column('sources', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('year_range', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('result_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_search_queries_id', 'search_queries', ['id'])
    op.create_index('ix_search_queries_search_id', 'search_queries', ['search_id'])

    # Datasets
    op.create_table(
        'datasets',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('format', sa.String(length=50), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('column_count', sa.Integer(), nullable=True),
        sa.Column('schema_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_datasets_id', 'datasets', ['id'])
    op.create_index('ix_datasets_project_id', 'datasets', ['project_id'])

    # Analysis Runs
    op.create_table(
        'analysis_runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('hypothesis_id', sa.String(), nullable=True),
        sa.Column('dataset_id', sa.String(), nullable=True),
        sa.Column('script', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_analysis_runs_id', 'analysis_runs', ['id'])
    op.create_index('ix_analysis_runs_hypothesis_id', 'analysis_runs', ['hypothesis_id'])
    op.create_index('ix_analysis_runs_dataset_id', 'analysis_runs', ['dataset_id'])

    # Analysis Artifacts
    op.create_table(
        'analysis_artifacts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('analysis_run_id', sa.String(), nullable=False),
        sa.Column('artifact_type', sa.String(length=50), nullable=True),
        sa.Column('file_path', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_analysis_artifacts_id', 'analysis_artifacts', ['id'])
    op.create_index('ix_analysis_artifacts_analysis_run_id', 'analysis_artifacts', ['analysis_run_id'])

    # Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=True),
        sa.Column('run_id', sa.String(), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('actor', sa.String(length=100), nullable=True),
        sa.Column('action', sa.Text(), nullable=True),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'])
    op.create_index('ix_audit_logs_project_id', 'audit_logs', ['project_id'])
    op.create_index('ix_audit_logs_run_id', 'audit_logs', ['run_id'])
    op.create_index('ix_audit_logs_event_type', 'audit_logs', ['event_type'])

    # Approval Requests
    op.create_table(
        'approval_requests',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=True),
        sa.Column('run_id', sa.String(), nullable=True),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('action_description', sa.Text(), nullable=True),
        sa.Column('action_payload', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('reviewer_notes', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_approval_requests_id', 'approval_requests', ['id'])
    op.create_index('ix_approval_requests_project_id', 'approval_requests', ['project_id'])
    op.create_index('ix_approval_requests_run_id', 'approval_requests', ['run_id'])
    op.create_index('ix_approval_requests_status', 'approval_requests', ['status'])

    # System Events
    op.create_table(
        'system_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_system_events_id', 'system_events', ['id'])
    op.create_index('ix_system_events_event_type', 'system_events', ['event_type'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('system_events')
    op.drop_table('approval_requests')
    op.drop_table('audit_logs')
    op.drop_table('analysis_artifacts')
    op.drop_table('analysis_runs')
    op.drop_table('datasets')
    op.drop_table('search_queries')
    op.drop_table('literature_searches')
    op.drop_table('knowledge_notes')
    op.drop_table('research_reports')
    op.drop_table('skill_evaluations')
    op.drop_table('skill_usages')
    op.drop_table('skill_versions')
    op.drop_table('skills')
    op.drop_table('validation_plans')
    op.drop_table('hypotheses')
    op.drop_table('research_questions')
    op.drop_table('cluster_conflicts')
    op.drop_table('cluster_labels')
    op.drop_table('paper_clusters')
    op.drop_table('paper_analyses')
    op.drop_table('paper_embeddings')
    op.drop_table('paper_fulltexts')
    op.drop_table('paper_sources')
    op.drop_table('papers')
    op.drop_table('idle_cycles')
    op.drop_table('tool_calls')
    op.drop_table('research_run_events')
    op.drop_table('research_runs')
    op.drop_table('idea_decisions')
    op.drop_table('idea_classifications')
    op.drop_table('idea_scores')
    op.drop_table('idea_versions')
    op.drop_table('ideas')
    op.drop_table('projects')
