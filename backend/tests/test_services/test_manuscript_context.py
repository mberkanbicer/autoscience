"""Tests for manuscript context assembly."""

import pytest
from uuid import uuid4

from app.engine.manuscript_engine import ManuscriptGenerator
from app.models.idea import Idea
from app.models.project import Project
from app.models.paper import Paper, PaperCluster
from app.models.report import AnalysisArtifact, AnalysisRun
from app.models.research_question import Hypothesis
from app.models.research_run import ResearchRun
from app.services.manuscript_context_service import ManuscriptContextService


@pytest.mark.asyncio
async def test_build_generation_params_uses_experiment_stdout(db_session):
    project_id = str(uuid4())
    run_id = str(uuid4())
    idea_id = str(uuid4())
    paper_id = str(uuid4())
    cluster_id = str(uuid4())

    db_session.add(
        Project(
            id=project_id,
            name="Manuscript Test Project",
            domain="ML",
            default_flexibility=0.6,
            idle_research_enabled=False,
            idle_trigger_minutes=120,
            max_idle_cycles_per_day=3,
            max_sources_per_cycle=50,
            approval_required_for_external_actions=True,
        )
    )
    db_session.add(
        ResearchRun(
            id=run_id,
            project_id=project_id,
            idea_id=idea_id,
            run_type="user_directed",
            state="completed",
        )
    )
    db_session.add(
        Idea(
            id=idea_id,
            project_id=project_id,
            origin="user",
            initial_text="Study transformer efficiency",
            current_text="Study transformer efficiency under low-data regimes",
            status="active",
        )
    )
    db_session.add(
        Paper(
            id=paper_id,
            project_id=project_id,
            title="Efficient Transformers",
            authors=["Smith, J."],
            year=2024,
            venue="NeurIPS",
            doi="10.1234/example",
            abstract="We study efficient transformer variants.",
        )
    )
    db_session.add(
        PaperCluster(
            id=cluster_id,
            project_id=project_id,
            run_id=run_id,
            name="Efficiency Cluster",
            description="Papers about efficient transformers",
            paper_ids=[paper_id],
        )
    )
    db_session.add(
        Hypothesis(
            id=str(uuid4()),
            project_id=project_id,
            statement="Low-data training improves generalization.",
            confidence=0.7,
            status="draft",
        )
    )

    analysis_run_id = str(uuid4())
    db_session.add(
        AnalysisRun(
            id=analysis_run_id,
            run_id=run_id,
            script="print('Correlation: 0.42')",
            status="completed",
        )
    )
    db_session.add(
        AnalysisArtifact(
            id=str(uuid4()),
            analysis_run_id=analysis_run_id,
            artifact_type="stdout",
            description="Correlation: 0.42\nP-Value: 0.01",
        )
    )
    await db_session.flush()

    service = ManuscriptContextService(db_session)
    params = await service.build_generation_params(run_id)

    assert "Efficient Transformers" in params.findings[0]
    assert params.papers[0]["doi"] == "10.1234/example"
    assert any(result["metric"] == "experiment_output" for result in params.validation_results)
    assert params.method_description is not None


def test_assemble_latex_document_includes_abstract_and_bibliography():
    latex = ManuscriptGenerator.assemble_latex_document(
        {
            "title": "Test Study",
            "abstract": "This is the abstract.",
            "sections": [{"title": "1. Introduction", "content": "Intro body"}],
        }
    )

    assert "\\begin{abstract}" in latex
    assert "This is the abstract." in latex
    assert "\\bibliography{references}" in latex


def test_citation_key_is_stable():
    key = ManuscriptGenerator.citation_key({"id": "abc12345-6789", "year": 2024})
    assert key.startswith("paper_abc12345_")