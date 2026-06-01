"""Add CASCADE delete to all foreign key relationships

Revision ID: 004
Revises: 003_add_parent_idea_id
Create Date: 2026-06-01 11:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection

# revision identifiers, used by Alembic.
revision = '004_add_cascade_deletes'
down_revision = '003_add_parent_idea_id'
branch_labels = None
depends_on = None


def upgrade():
    """Add CASCADE delete to all foreign key relationships."""
    
    # Get the database connection
    bind = op.get_bind()
    inspector = reflection.Inspector.from_engine(bind)
    
    # Tables to update with CASCADE deletes
    # Format: (table_name, constraint_name, fk_columns, ref_table, ondelete_action)
    
    # research_runs table
    op.execute("ALTER TABLE research_runs "
               "DROP CONSTRAINT IF EXISTS research_runs_project_id_fkey")
    op.execute("ALTER TABLE research_runs "
               "ADD CONSTRAINT research_runs_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE")
    
    op.execute("ALTER TABLE research_runs "
               "DROP CONSTRAINT IF EXISTS research_runs_idea_id_fkey")
    op.execute("ALTER TABLE research_runs "
               "ADD CONSTRAINT research_runs_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE SET NULL")
    
    # research_run_events table
    op.execute("ALTER TABLE research_run_events "
               "DROP CONSTRAINT IF EXISTS research_run_events_run_id_fkey")
    op.execute("ALTER TABLE research_run_events "
               "ADD CONSTRAINT research_run_events_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id) ON DELETE CASCADE")
    
    # tool_calls table
    op.execute("ALTER TABLE tool_calls "
               "DROP CONSTRAINT IF EXISTS tool_calls_run_id_fkey")
    op.execute("ALTER TABLE tool_calls "
               "ADD CONSTRAINT tool_calls_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id) ON DELETE CASCADE")
    
    # idle_cycles table
    op.execute("ALTER TABLE idle_cycles "
               "DROP CONSTRAINT IF EXISTS idle_cycles_project_id_fkey")
    op.execute("ALTER TABLE idle_cycles "
               "ADD CONSTRAINT idle_cycles_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE")
    
    op.execute("ALTER TABLE idle_cycles "
               "DROP CONSTRAINT IF EXISTS idle_cycles_run_id_fkey")
    op.execute("ALTER TABLE idle_cycles "
               "ADD CONSTRAINT idle_cycles_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id) ON DELETE SET NULL")
    
    # ideas table
    op.execute("ALTER TABLE ideas "
               "DROP CONSTRAINT IF EXISTS ideas_project_id_fkey")
    op.execute("ALTER TABLE ideas "
               "ADD CONSTRAINT ideas_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE")
    
    op.execute("ALTER TABLE ideas "
               "DROP CONSTRAINT IF EXISTS ideas_parent_idea_id_fkey")
    op.execute("ALTER TABLE ideas "
               "ADD CONSTRAINT ideas_parent_idea_id_fkey "
               "FOREIGN KEY (parent_idea_id) REFERENCES ideas(id) ON DELETE SET NULL")
    
    # idea_versions table
    op.execute("ALTER TABLE idea_versions "
               "DROP CONSTRAINT IF EXISTS idea_versions_idea_id_fkey")
    op.execute("ALTER TABLE idea_versions "
               "ADD CONSTRAINT idea_versions_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE CASCADE")
    
    # idea_scores table
    op.execute("ALTER TABLE idea_scores "
               "DROP CONSTRAINT IF EXISTS idea_scores_idea_id_fkey")
    op.execute("ALTER TABLE idea_scores "
               "ADD CONSTRAINT idea_scores_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE CASCADE")
    
    # idea_classifications table
    op.execute("ALTER TABLE idea_classifications "
               "DROP CONSTRAINT IF EXISTS idea_classifications_idea_id_fkey")
    op.execute("ALTER TABLE idea_classifications "
               "ADD CONSTRAINT idea_classifications_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE CASCADE")
    
    # idea_decisions table
    op.execute("ALTER TABLE idea_decisions "
               "DROP CONSTRAINT IF EXISTS idea_decisions_idea_id_fkey")
    op.execute("ALTER TABLE idea_decisions "
               "ADD CONSTRAINT idea_decisions_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE CASCADE")
    
    op.execute("ALTER TABLE idea_decisions "
               "DROP CONSTRAINT IF EXISTS idea_decisions_run_id_fkey")
    op.execute("ALTER TABLE idea_decisions "
               "ADD CONSTRAINT idea_decisions_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id) ON DELETE SET NULL")
    
    # research_questions table
    op.execute("ALTER TABLE research_questions "
               "DROP CONSTRAINT IF EXISTS research_questions_project_id_fkey")
    op.execute("ALTER TABLE research_questions "
               "ADD CONSTRAINT research_questions_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE")
    
    op.execute("ALTER TABLE research_questions "
               "DROP CONSTRAINT IF EXISTS research_questions_idea_id_fkey")
    op.execute("ALTER TABLE research_questions "
               "ADD CONSTRAINT research_questions_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE SET NULL")
    
    op.execute("ALTER TABLE research_questions "
               "DROP CONSTRAINT IF EXISTS research_questions_run_id_fkey")
    op.execute("ALTER TABLE research_questions "
               "ADD CONSTRAINT research_questions_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id) ON DELETE SET NULL")
    
    # hypotheses table
    op.execute("ALTER TABLE hypotheses "
               "DROP CONSTRAINT IF EXISTS hypotheses_project_id_fkey")
    op.execute("ALTER TABLE hypotheses "
               "ADD CONSTRAINT hypotheses_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE")
    
    op.execute("ALTER TABLE hypotheses "
               "DROP CONSTRAINT IF EXISTS hypotheses_idea_id_fkey")
    op.execute("ALTER TABLE hypotheses "
               "ADD CONSTRAINT hypotheses_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE SET NULL")
    
    op.execute("ALTER TABLE hypotheses "
               "DROP CONSTRAINT IF EXISTS hypotheses_question_id_fkey")
    op.execute("ALTER TABLE hypotheses "
               "ADD CONSTRAINT hypotheses_question_id_fkey "
               "FOREIGN KEY (question_id) REFERENCES research_questions(id) ON DELETE SET NULL")
    
    # validation_plans table
    op.execute("ALTER TABLE validation_plans "
               "DROP CONSTRAINT IF EXISTS validation_plans_hypothesis_id_fkey")
    op.execute("ALTER TABLE validation_plans "
               "ADD CONSTRAINT validation_plans_hypothesis_id_fkey "
               "FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id) ON DELETE CASCADE")
    
    # papers table
    op.execute("ALTER TABLE papers "
               "DROP CONSTRAINT IF EXISTS papers_project_id_fkey")
    op.execute("ALTER TABLE papers "
               "ADD CONSTRAINT papers_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE")
    
    # paper_sources table
    op.execute("ALTER TABLE paper_sources "
               "DROP CONSTRAINT IF EXISTS paper_sources_paper_id_fkey")
    op.execute("ALTER TABLE paper_sources "
               "ADD CONSTRAINT paper_sources_paper_id_fkey "
               "FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE")
    
    # paper_fulltexts table
    op.execute("ALTER TABLE paper_fulltexts "
               "DROP CONSTRAINT IF EXISTS paper_fulltexts_paper_id_fkey")
    op.execute("ALTER TABLE paper_fulltexts "
               "ADD CONSTRAINT paper_fulltexts_paper_id_fkey "
               "FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE")
    
    # paper_embeddings table
    op.execute("ALTER TABLE paper_embeddings "
               "DROP CONSTRAINT IF EXISTS paper_embeddings_paper_id_fkey")
    op.execute("ALTER TABLE paper_embeddings "
               "ADD CONSTRAINT paper_embeddings_paper_id_fkey "
               "FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE")
    
    # paper_analyses table
    op.execute("ALTER TABLE paper_analyses "
               "DROP CONSTRAINT IF EXISTS paper_analyses_paper_id_fkey")
    op.execute("ALTER TABLE paper_analyses "
               "ADD CONSTRAINT paper_analyses_paper_id_fkey "
               "FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE")
    
    # paper_clusters table
    op.execute("ALTER TABLE paper_clusters "
               "DROP CONSTRAINT IF EXISTS paper_clusters_project_id_fkey")
    op.execute("ALTER TABLE paper_clusters "
               "ADD CONSTRAINT paper_clusters_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE")
    
    # cluster_labels table
    op.execute("ALTER TABLE cluster_labels "
               "DROP CONSTRAINT IF EXISTS cluster_labels_cluster_id_fkey")
    op.execute("ALTER TABLE cluster_labels "
               "ADD CONSTRAINT cluster_labels_cluster_id_fkey "
               "FOREIGN KEY (cluster_id) REFERENCES paper_clusters(id) ON DELETE CASCADE")
    
    # cluster_conflicts table
    op.execute("ALTER TABLE cluster_conflicts "
               "DROP CONSTRAINT IF EXISTS cluster_conflicts_project_id_fkey")
    op.execute("ALTER TABLE cluster_conflicts "
               "ADD CONSTRAINT cluster_conflicts_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE")
    
    op.execute("ALTER TABLE cluster_conflicts "
               "DROP CONSTRAINT IF EXISTS cluster_conflicts_cluster_id_fkey")
    op.execute("ALTER TABLE cluster_conflicts "
               "ADD CONSTRAINT cluster_conflicts_cluster_id_fkey "
               "FOREIGN KEY (cluster_id) REFERENCES paper_clusters(id) ON DELETE CASCADE")
    
    # research_reports table
    op.execute("ALTER TABLE research_reports "
               "DROP CONSTRAINT IF EXISTS research_reports_project_id_fkey")
    op.execute("ALTER TABLE research_reports "
               "ADD CONSTRAINT research_reports_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE")
    
    op.execute("ALTER TABLE research_reports "
               "DROP CONSTRAINT IF EXISTS research_reports_run_id_fkey")
    op.execute("ALTER TABLE research_reports "
               "ADD CONSTRAINT research_reports_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id) ON DELETE SET NULL")
    
    op.execute("ALTER TABLE research_reports "
               "DROP CONSTRAINT IF EXISTS research_reports_idea_id_fkey")
    op.execute("ALTER TABLE research_reports "
               "ADD CONSTRAINT research_reports_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE SET NULL")
    
    # knowledge_notes table
    op.execute("ALTER TABLE knowledge_notes "
               "DROP CONSTRAINT IF EXISTS knowledge_notes_project_id_fkey")
    op.execute("ALTER TABLE knowledge_notes "
               "ADD CONSTRAINT knowledge_notes_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE")
    
    # literature_searches table
    op.execute("ALTER TABLE literature_searches "
               "DROP CONSTRAINT IF EXISTS literature_searches_project_id_fkey")
    op.execute("ALTER TABLE literature_searches "
               "ADD CONSTRAINT literature_searches_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE")
    
    op.execute("ALTER TABLE literature_searches "
               "DROP CONSTRAINT IF EXISTS literature_searches_run_id_fkey")
    op.execute("ALTER TABLE literature_searches "
               "ADD CONSTRAINT literature_searches_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id) ON DELETE SET NULL")
    
    op.execute("ALTER TABLE literature_searches "
               "DROP CONSTRAINT IF EXISTS literature_searches_idea_id_fkey")
    op.execute("ALTER TABLE literature_searches "
               "ADD CONSTRAINT literature_searches_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE SET NULL")
    
    # search_queries table
    op.execute("ALTER TABLE search_queries "
               "DROP CONSTRAINT IF EXISTS search_queries_search_id_fkey")
    op.execute("ALTER TABLE search_queries "
               "ADD CONSTRAINT search_queries_search_id_fkey "
               "FOREIGN KEY (search_id) REFERENCES literature_searches(id) ON DELETE CASCADE")
    
    # datasets table
    op.execute("ALTER TABLE datasets "
               "DROP CONSTRAINT IF EXISTS datasets_project_id_fkey")
    op.execute("ALTER TABLE datasets "
               "ADD CONSTRAINT datasets_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE")
    
    # analysis_runs table
    op.execute("ALTER TABLE analysis_runs "
               "DROP CONSTRAINT IF EXISTS analysis_runs_hypothesis_id_fkey")
    op.execute("ALTER TABLE analysis_runs "
               "ADD CONSTRAINT analysis_runs_hypothesis_id_fkey "
               "FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id) ON DELETE SET NULL")
    
    op.execute("ALTER TABLE analysis_runs "
               "DROP CONSTRAINT IF EXISTS analysis_runs_dataset_id_fkey")
    op.execute("ALTER TABLE analysis_runs "
               "ADD CONSTRAINT analysis_runs_dataset_id_fkey "
               "FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE SET NULL")
    
    # analysis_artifacts table
    op.execute("ALTER TABLE analysis_artifacts "
               "DROP CONSTRAINT IF EXISTS analysis_artifacts_analysis_run_id_fkey")
    op.execute("ALTER TABLE analysis_artifacts "
               "ADD CONSTRAINT analysis_artifacts_analysis_run_id_fkey "
               "FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE")
    
    # audit_logs table
    op.execute("ALTER TABLE audit_logs "
               "DROP CONSTRAINT IF EXISTS audit_logs_project_id_fkey")
    op.execute("ALTER TABLE audit_logs "
               "ADD CONSTRAINT audit_logs_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL")
    
    op.execute("ALTER TABLE audit_logs "
               "DROP CONSTRAINT IF EXISTS audit_logs_run_id_fkey")
    op.execute("ALTER TABLE audit_logs "
               "ADD CONSTRAINT audit_logs_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id) ON DELETE SET NULL")
    
    # approval_requests table
    op.execute("ALTER TABLE approval_requests "
               "DROP CONSTRAINT IF EXISTS approval_requests_project_id_fkey")
    op.execute("ALTER TABLE approval_requests "
               "ADD CONSTRAINT approval_requests_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects.id) ON DELETE SET NULL")
    
    op.execute("ALTER TABLE approval_requests "
               "DROP CONSTRAINT IF EXISTS approval_requests_run_id_fkey")
    op.execute("ALTER TABLE approval_requests "
               "ADD CONSTRAINT approval_requests_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id) ON DELETE SET NULL")
    
    # skills table
    op.execute("ALTER TABLE skills "
               "DROP CONSTRAINT IF EXISTS skills_project_id_fkey")
    op.execute("ALTER TABLE skills "
               "ADD CONSTRAINT skills_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL")
    
    # skill_versions table
    op.execute("ALTER TABLE skill_versions "
               "DROP CONSTRAINT IF EXISTS skill_versions_skill_id_fkey")
    op.execute("ALTER TABLE skill_versions "
               "ADD CONSTRAINT skill_versions_skill_id_fkey "
               "FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE")
    
    # skill_usages table
    op.execute("ALTER TABLE skill_usages "
               "DROP CONSTRAINT IF EXISTS skill_usages_skill_id_fkey")
    op.execute("ALTER TABLE skill_usages "
               "ADD CONSTRAINT skill_usages_skill_id_fkey "
               "FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE")
    
    op.execute("ALTER TABLE skill_usages "
               "DROP CONSTRAINT IF EXISTS skill_usages_run_id_fkey")
    op.execute("ALTER TABLE skill_usages "
               "ADD CONSTRAINT skill_usages_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id) ON DELETE SET NULL")
    
    # skill_evaluations table
    op.execute("ALTER TABLE skill_evaluations "
               "DROP CONSTRAINT IF EXISTS skill_evaluations_skill_id_fkey")
    op.execute("ALTER TABLE skill_evaluations "
               "ADD CONSTRAINT skill_evaluations_skill_id_fkey "
               "FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE")


def downgrade():
    """Remove CASCADE delete from all foreign key relationships."""
    
    # Revert to NO ACTION (PostgreSQL default)
    
    # research_runs table
    op.execute("ALTER TABLE research_runs "
               "DROP CONSTRAINT IF EXISTS research_runs_project_id_fkey")
    op.execute("ALTER TABLE research_runs "
               "ADD CONSTRAINT research_runs_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id)")
    
    op.execute("ALTER TABLE research_runs "
               "DROP CONSTRAINT IF EXISTS research_runs_idea_id_fkey")
    op.execute("ALTER TABLE research_runs "
               "ADD CONSTRAINT research_runs_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id)")
    
    # research_run_events table
    op.execute("ALTER TABLE research_run_events "
               "DROP CONSTRAINT IF EXISTS research_run_events_run_id_fkey")
    op.execute("ALTER TABLE research_run_events "
               "ADD CONSTRAINT research_run_events_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id)")
    
    # tool_calls table
    op.execute("ALTER TABLE tool_calls "
               "DROP CONSTRAINT IF EXISTS tool_calls_run_id_fkey")
    op.execute("ALTER TABLE tool_calls "
               "ADD CONSTRAINT tool_calls_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id)")
    
    # idle_cycles table
    op.execute("ALTER TABLE idle_cycles "
               "DROP CONSTRAINT IF EXISTS idle_cycles_project_id_fkey")
    op.execute("ALTER TABLE idle_cycles "
               "ADD CONSTRAINT idle_cycles_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id)")
    
    op.execute("ALTER TABLE idle_cycles "
               "DROP CONSTRAINT IF EXISTS idle_cycles_run_id_fkey")
    op.execute("ALTER TABLE idle_cycles "
               "ADD CONSTRAINT idle_cycles_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id)")
    
    # ideas table
    op.execute("ALTER TABLE ideas "
               "DROP CONSTRAINT IF EXISTS ideas_project_id_fkey")
    op.execute("ALTER TABLE ideas "
               "ADD CONSTRAINT ideas_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id)")
    
    op.execute("ALTER TABLE ideas "
               "DROP CONSTRAINT IF EXISTS ideas_parent_idea_id_fkey")
    op.execute("ALTER TABLE ideas "
               "ADD CONSTRAINT ideas_parent_idea_id_fkey "
               "FOREIGN KEY (parent_idea_id) REFERENCES ideas(id)")
    
    # idea_versions table
    op.execute("ALTER TABLE idea_versions "
               "DROP CONSTRAINT IF EXISTS idea_versions_idea_id_fkey")
    op.execute("ALTER TABLE idea_versions "
               "ADD CONSTRAINT idea_versions_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id)")
    
    # idea_scores table
    op.execute("ALTER TABLE idea_scores "
               "DROP CONSTRAINT IF EXISTS idea_scores_idea_id_fkey")
    op.execute("ALTER TABLE idea_scores "
               "ADD CONSTRAINT idea_scores_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id)")
    
    # idea_classifications table
    op.execute("ALTER TABLE idea_classifications "
               "DROP CONSTRAINT IF EXISTS idea_classifications_idea_id_fkey")
    op.execute("ALTER TABLE idea_classifications "
               "ADD CONSTRAINT idea_classifications_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id)")
    
    # idea_decisions table
    op.execute("ALTER TABLE idea_decisions "
               "DROP CONSTRAINT IF EXISTS idea_decisions_idea_id_fkey")
    op.execute("ALTER TABLE idea_decisions "
               "ADD CONSTRAINT idea_decisions_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id)")
    
    op.execute("ALTER TABLE idea_decisions "
               "DROP CONSTRAINT IF EXISTS idea_decisions_run_id_fkey")
    op.execute("ALTER TABLE idea_decisions "
               "ADD CONSTRAINT idea_decisions_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id)")
    
    # research_questions table
    op.execute("ALTER TABLE research_questions "
               "DROP CONSTRAINT IF EXISTS research_questions_project_id_fkey")
    op.execute("ALTER TABLE research_questions "
               "ADD CONSTRAINT research_questions_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id)")
    
    op.execute("ALTER TABLE research_questions "
               "DROP CONSTRAINT IF EXISTS research_questions_idea_id_fkey")
    op.execute("ALTER TABLE research_questions "
               "ADD CONSTRAINT research_questions_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id)")
    
    op.execute("ALTER TABLE research_questions "
               "DROP CONSTRAINT IF EXISTS research_questions_run_id_fkey")
    op.execute("ALTER TABLE research_questions "
               "ADD CONSTRAINT research_questions_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id)")
    
    # hypotheses table
    op.execute("ALTER TABLE hypotheses "
               "DROP CONSTRAINT IF EXISTS hypotheses_project_id_fkey")
    op.execute("ALTER TABLE hypotheses "
               "ADD CONSTRAINT hypotheses_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id)")
    
    op.execute("ALTER TABLE hypotheses "
               "DROP CONSTRAINT IF EXISTS hypotheses_idea_id_fkey")
    op.execute("ALTER TABLE hypotheses "
               "ADD CONSTRAINT hypotheses_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id)")
    
    op.execute("ALTER TABLE hypotheses "
               "DROP CONSTRAINT IF EXISTS hypotheses_question_id_fkey")
    op.execute("ALTER TABLE hypotheses "
               "ADD CONSTRAINT hypotheses_question_id_fkey "
               "FOREIGN KEY (question_id) REFERENCES research_questions(id)")
    
    # validation_plans table
    op.execute("ALTER TABLE validation_plans "
               "DROP CONSTRAINT IF EXISTS validation_plans_hypothesis_id_fkey")
    op.execute("ALTER TABLE validation_plans "
               "ADD CONSTRAINT validation_plans_hypothesis_id_fkey "
               "FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)")
    
    # papers table
    op.execute("ALTER TABLE papers "
               "DROP CONSTRAINT IF EXISTS papers_project_id_fkey")
    op.execute("ALTER TABLE papers "
               "ADD CONSTRAINT papers_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id)")
    
    # paper_sources table
    op.execute("ALTER TABLE paper_sources "
               "DROP CONSTRAINT IF EXISTS paper_sources_paper_id_fkey")
    op.execute("ALTER TABLE paper_sources "
               "ADD CONSTRAINT paper_sources_paper_id_fkey "
               "FOREIGN KEY (paper_id) REFERENCES papers(id)")
    
    # paper_fulltexts table
    op.execute("ALTER TABLE paper_fulltexts "
               "DROP CONSTRAINT IF EXISTS paper_fulltexts_paper_id_fkey")
    op.execute("ALTER TABLE paper_fulltexts "
               "ADD CONSTRAINT paper_fulltexts_paper_id_fkey "
               "FOREIGN KEY (paper_id) REFERENCES papers(id)")
    
    # paper_embeddings table
    op.execute("ALTER TABLE paper_embeddings "
               "DROP CONSTRAINT IF EXISTS paper_embeddings_paper_id_fkey")
    op.execute("ALTER TABLE paper_embeddings "
               "ADD CONSTRAINT paper_embeddings_paper_id_fkey "
               "FOREIGN KEY (paper_id) REFERENCES papers(id)")
    
    # paper_analyses table
    op.execute("ALTER TABLE paper_analyses "
               "DROP CONSTRAINT IF EXISTS paper_analyses_paper_id_fkey")
    op.execute("ALTER TABLE paper_analyses "
               "ADD CONSTRAINT paper_analyses_paper_id_fkey "
               "FOREIGN KEY (paper_id) REFERENCES papers(id)")
    
    # paper_clusters table
    op.execute("ALTER TABLE paper_clusters "
               "DROP CONSTRAINT IF EXISTS paper_clusters_project_id_fkey")
    op.execute("ALTER TABLE paper_clusters "
               "ADD CONSTRAINT paper_clusters_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id)")
    
    # cluster_labels table
    op.execute("ALTER TABLE cluster_labels "
               "DROP CONSTRAINT IF EXISTS cluster_labels_cluster_id_fkey")
    op.execute("ALTER TABLE cluster_labels "
               "ADD CONSTRAINT cluster_labels_cluster_id_fkey "
               "FOREIGN KEY (cluster_id) REFERENCES paper_clusters(id)")
    
    # cluster_conflicts table
    op.execute("ALTER TABLE cluster_conflicts "
               "DROP CONSTRAINT IF EXISTS cluster_conflicts_project_id_fkey")
    op.execute("ALTER TABLE cluster_conflicts "
               "ADD CONSTRAINT cluster_conflicts_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id)")
    
    op.execute("ALTER TABLE cluster_conflicts "
               "DROP CONSTRAINT IF EXISTS cluster_conflicts_cluster_id_fkey")
    op.execute("ALTER TABLE cluster_conflicts "
               "ADD CONSTRAINT cluster_conflicts_cluster_id_fkey "
               "FOREIGN KEY (cluster_id) REFERENCES paper_clusters(id)")
    
    # research_reports table
    op.execute("ALTER TABLE research_reports "
               "DROP CONSTRAINT IF EXISTS research_reports_project_id_fkey")
    op.execute("ALTER TABLE research_reports "
               "ADD CONSTRAINT research_reports_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id)")
    
    op.execute("ALTER TABLE research_reports "
               "DROP CONSTRAINT IF EXISTS research_reports_run_id_fkey")
    op.execute("ALTER TABLE research_reports "
               "ADD CONSTRAINT research_reports_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id)")
    
    op.execute("ALTER TABLE research_reports "
               "DROP CONSTRAINT IF EXISTS research_reports_idea_id_fkey")
    op.execute("ALTER TABLE research_reports "
               "ADD CONSTRAINT research_reports_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id)")
    
    # knowledge_notes table
    op.execute("ALTER TABLE knowledge_notes "
               "DROP CONSTRAINT IF EXISTS knowledge_notes_project_id_fkey")
    op.execute("ALTER TABLE knowledge_notes "
               "ADD CONSTRAINT knowledge_notes_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id)")
    
    # literature_searches table
    op.execute("ALTER TABLE literature_searches "
               "DROP CONSTRAINT IF EXISTS literature_searches_project_id_fkey")
    op.execute("ALTER TABLE literature_searches "
               "ADD CONSTRAINT literature_searches_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id)")
    
    op.execute("ALTER TABLE literature_searches "
               "DROP CONSTRAINT IF EXISTS literature_searches_run_id_fkey")
    op.execute("ALTER TABLE literature_searches "
               "ADD CONSTRAINT literature_searches_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id)")
    
    op.execute("ALTER TABLE literature_searches "
               "DROP CONSTRAINT IF EXISTS literature_searches_idea_id_fkey")
    op.execute("ALTER TABLE literature_searches "
               "ADD CONSTRAINT literature_searches_idea_id_fkey "
               "FOREIGN KEY (idea_id) REFERENCES ideas(id)")
    
    # search_queries table
    op.execute("ALTER TABLE search_queries "
               "DROP CONSTRAINT IF EXISTS search_queries_search_id_fkey")
    op.execute("ALTER TABLE search_queries "
               "ADD CONSTRAINT search_queries_search_id_fkey "
               "FOREIGN KEY (search_id) REFERENCES literature_searches(id)")
    
    # datasets table
    op.execute("ALTER TABLE datasets "
               "DROP CONSTRAINT IF EXISTS datasets_project_id_fkey")
    op.execute("ALTER TABLE datasets "
               "ADD CONSTRAINT datasets_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id)")
    
    # analysis_runs table
    op.execute("ALTER TABLE analysis_runs "
               "DROP CONSTRAINT IF EXISTS analysis_runs_hypothesis_id_fkey")
    op.execute("ALTER TABLE analysis_runs "
               "ADD CONSTRAINT analysis_runs_hypothesis_id_fkey "
               "FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)")
    
    op.execute("ALTER TABLE analysis_runs "
               "DROP CONSTRAINT IF EXISTS analysis_runs_dataset_id_fkey")
    op.execute("ALTER TABLE analysis_runs "
               "ADD CONSTRAINT analysis_runs_dataset_id_fkey "
               "FOREIGN KEY (dataset_id) REFERENCES datasets(id)")
    
    # analysis_artifacts table
    op.execute("ALTER TABLE analysis_artifacts "
               "DROP CONSTRAINT IF EXISTS analysis_artifacts_analysis_run_id_fkey")
    op.execute("ALTER TABLE analysis_artifacts "
               "ADD CONSTRAINT analysis_artifacts_analysis_run_id_fkey "
               "FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id)")
    
    # audit_logs table
    op.execute("ALTER TABLE audit_logs "
               "DROP CONSTRAINT IF EXISTS audit_logs_project_id_fkey")
    op.execute("ALTER TABLE audit_logs "
               "ADD CONSTRAINT audit_logs_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id)")
    
    op.execute("ALTER TABLE audit_logs "
               "DROP CONSTRAINT IF EXISTS audit_logs_run_id_fkey")
    op.execute("ALTER TABLE audit_logs "
               "ADD CONSTRAINT audit_logs_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id)")
    
    # approval_requests table
    op.execute("ALTER TABLE approval_requests "
               "DROP CONSTRAINT IF EXISTS approval_requests_project_id_fkey")
    op.execute("ALTER TABLE approval_requests "
               "ADD CONSTRAINT approval_requests_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id)")
    
    op.execute("ALTER TABLE approval_requests "
               "DROP CONSTRAINT IF EXISTS approval_requests_run_id_fkey")
    op.execute("ALTER TABLE approval_requests "
               "ADD CONSTRAINT approval_requests_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id)")
    
    # skills table
    op.execute("ALTER TABLE skills "
               "DROP CONSTRAINT IF EXISTS skills_project_id_fkey")
    op.execute("ALTER TABLE skills "
               "ADD CONSTRAINT skills_project_id_fkey "
               "FOREIGN KEY (project_id) REFERENCES projects(id)")
    
    # skill_versions table
    op.execute("ALTER TABLE skill_versions "
               "DROP CONSTRAINT IF EXISTS skill_versions_skill_id_fkey")
    op.execute("ALTER TABLE skill_versions "
               "ADD CONSTRAINT skill_versions_skill_id_fkey "
               "FOREIGN KEY (skill_id) REFERENCES skills(id)")
    
    # skill_usages table
    op.execute("ALTER TABLE skill_usages "
               "DROP CONSTRAINT IF EXISTS skill_usages_skill_id_fkey")
    op.execute("ALTER TABLE skill_usages "
               "ADD CONSTRAINT skill_usages_skill_id_fkey "
               "FOREIGN KEY (skill_id) REFERENCES skills(id)")
    
    op.execute("ALTER TABLE skill_usages "
               "DROP CONSTRAINT IF EXISTS skill_usages_run_id_fkey")
    op.execute("ALTER TABLE skill_usages "
               "ADD CONSTRAINT skill_usages_run_id_fkey "
               "FOREIGN KEY (run_id) REFERENCES research_runs(id)")
    
    # skill_evaluations table
    op.execute("ALTER TABLE skill_evaluations "
               "DROP CONSTRAINT IF EXISTS skill_evaluations_skill_id_fkey")
    op.execute("ALTER TABLE skill_evaluations "
               "ADD CONSTRAINT skill_evaluations_skill_id_fkey "
               "FOREIGN KEY (skill_id) REFERENCES skills(id)")