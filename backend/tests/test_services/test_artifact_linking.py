"""Tests for cross-mode artifact linking between experiment results and manuscript sections."""

from __future__ import annotations

import pytest
from uuid import uuid4
from datetime import datetime

from sqlalchemy import select

from app.models.report import Manuscript, ArtifactSectionLink, AnalysisArtifact, AnalysisRun
from app.services.artifact_linking_service import ArtifactLinkingService


@pytest.fixture
async def manuscript_fixtures(db_session):
    """Create a manuscript and related run/artifacts for testing."""
    from app.models.research_run import ResearchRun
    from app.models.project import Project
    from app.models.idea import Idea

    project = Project(
        id=str(uuid4()),
        name="Test Project",
        description="Test project for artifact linking",
    )
    db_session.add(project)

    idea = Idea(
        id=str(uuid4()),
        project_id=project.id,
        current_text="Test research idea",
    )
    db_session.add(idea)

    run = ResearchRun(
        id=str(uuid4()),
        project_id=project.id,
        idea_id=idea.id,
        state="completed",
    )
    db_session.add(run)

    manuscript = Manuscript(
        id=str(uuid4()),
        project_id=project.id,
        run_id=run.id,
        title="Test Manuscript",
        status="draft",
        version=1,
    )
    db_session.add(manuscript)

    analysis_run = AnalysisRun(
        id=str(uuid4()),
        run_id=run.id,
        hypothesis_id=str(uuid4()),
        script="print('hello')",
        status="completed",
    )
    db_session.add(analysis_run)

    artifact_figure = AnalysisArtifact(
        id=str(uuid4()),
        analysis_run_id=analysis_run.id,
        artifact_type="figure",
        file_path="/tmp/figures/plot.png",
        description="Accuracy comparison bar chart",
    )
    db_session.add(artifact_figure)

    artifact_table = AnalysisArtifact(
        id=str(uuid4()),
        analysis_run_id=analysis_run.id,
        artifact_type="table",
        file_path="/tmp/tables/results.csv",
        description="Experiment results summary table",
    )
    db_session.add(artifact_table)

    artifact_stdout = AnalysisArtifact(
        id=str(uuid4()),
        analysis_run_id=analysis_run.id,
        artifact_type="stdout",
        description="Accuracy: 0.942\nF1 score: 0.91\np = 0.003\nCohen's d = 0.72",
    )
    db_session.add(artifact_stdout)

    await db_session.flush()

    return {
        "project": project,
        "idea": idea,
        "run": run,
        "manuscript": manuscript,
        "analysis_run": analysis_run,
        "artifacts": {
            "figure": artifact_figure,
            "table": artifact_table,
            "stdout": artifact_stdout,
        },
    }


class TestArtifactLinkingService:
    """Tests for ArtifactLinkingService build and query operations."""

    @pytest.mark.asyncio
    async def test_build_links_with_experiment(self, db_session):
        """Verify links are built correctly from experiment data."""
        # Create a manuscript
        manuscript = Manuscript(
            id=str(uuid4()),
            project_id=str(uuid4()),
            run_id=str(uuid4()),
            title="Linked Manuscript",
            status="draft",
            version=1,
        )
        db_session.add(manuscript)
        await db_session.flush()

        service = ArtifactLinkingService(db_session)
        experiment = {
            "analysis_run_id": str(uuid4()),
            "success": True,
            "stdout": "Accuracy: 0.942\nF1 score: 0.91",
            "stderr": "",
            "artifacts": [
                {
                    "artifact_type": "figure",
                    "description": "Accuracy comparison chart",
                    "file_path": "/tmp/figures/acc.png",
                },
                {
                    "artifact_type": "table",
                    "description": "Results summary",
                    "file_path": "/tmp/tables/res.csv",
                },
                {
                    "artifact_type": "script",
                    "description": "analysis.py",
                },
            ],
        }
        claims = [
            {
                "statement": "Accuracy improved by 5.2%",
                "claim_type": "improvement",
                "confidence": 0.8,
                "evidence": "Accuracy increased from 0.89 to 0.942",
            },
            {
                "statement": "p = 0.003 (statistically significant)",
                "claim_type": "statistical",
                "confidence": 0.85,
                "evidence": "Two-sample t-test",
            },
        ]
        effect_sizes = [
            {
                "effect_type": "cohens_d",
                "value": 0.72,
                "label": "Cohen's d",
                "interpretation": "medium",
                "evidence": "d = 0.72",
            },
        ]

        result = await service.build_links(
            manuscript_id=manuscript.id,
            experiment=experiment,
            claims=claims,
            effect_sizes=effect_sizes,
        )

        assert result.links_created > 0
        assert len(result.sections_with_links) > 0
        assert "results" in result.sections_with_links
        assert len(result.artifact_types_linked) > 0

        # Verify links are persisted
        persisted = await db_session.execute(
            select(ArtifactSectionLink).where(
                ArtifactSectionLink.manuscript_id == manuscript.id
            )
        )
        links = list(persisted.scalars().all())
        assert len(links) == result.links_created

        # Check section assignment
        sections = {link.section for link in links}
        assert "results" in sections

        # Check artifact types
        types = {link.artifact_type for link in links}
        assert "figure" in types
        assert "table" in types
        assert "claim" in types
        assert "effect_size" in types

    @pytest.mark.asyncio
    async def test_build_links_idempotent(self, db_session):
        """Verify rebuilding links clears previous links first."""
        manuscript_id = str(uuid4())

        # Build first set of links
        service = ArtifactLinkingService(db_session)
        result1 = await service.build_links(
            manuscript_id=manuscript_id,
            experiment={
                "success": True,
                "stdout": "test output",
                "stderr": "",
                "artifacts": [],
            },
        )

        # Build second set with different data
        result2 = await service.build_links(
            manuscript_id=manuscript_id,
            experiment={
                "success": False,
                "stdout": "different",
                "stderr": "error msg",
                "artifacts": [],
            },
        )

        # Only the second set should exist
        persisted = await db_session.execute(
            select(ArtifactSectionLink).where(
                ArtifactSectionLink.manuscript_id == manuscript_id
            )
        )
        links = list(persisted.scalars().all())
        assert len(links) == result2.links_created

        # Check the data is from the second build (failed + stderr)
        source_summaries = [l.source_summary for l in links if l.source_summary]
        assert any("error" in (s or "").lower() for s in source_summaries) or any(
            "fail" in (s or "").lower() for s in source_summaries
        )

    @pytest.mark.asyncio
    async def test_get_links_for_manuscript(self, db_session):
        """Verify querying artifact links returns expected data."""
        manuscript_id = str(uuid4())

        service = ArtifactLinkingService(db_session)
        await service.build_links(
            manuscript_id=manuscript_id,
            experiment={
                "success": True,
                "stdout": "Accuracy: 0.95",
                "stderr": "",
                "artifacts": [],
            },
            claims=[
                {
                    "statement": "p = 0.002 significant",
                    "claim_type": "statistical",
                    "confidence": 0.85,
                    "evidence": "t-test result",
                },
            ],
        )

        # Query all links
        links = await service.get_links_for_manuscript(manuscript_id)
        assert len(links) > 0

        # Query by section
        results_links = await service.get_links_for_manuscript(
            manuscript_id, section="results"
        )
        assert len(results_links) > 0
        for link in results_links:
            assert link["section"] == "results"

        # Query by artifact type
        claim_links = await service.get_links_for_manuscript(
            manuscript_id, artifact_type="claim"
        )
        assert len(claim_links) > 0
        for link in claim_links:
            assert link["artifact_type"] == "claim"

    @pytest.mark.asyncio
    async def test_get_linked_artifacts_by_section(self, db_session):
        """Verify section-grouped query returns correct structure."""
        manuscript_id = str(uuid4())

        service = ArtifactLinkingService(db_session)
        await service.build_links(
            manuscript_id=manuscript_id,
            experiment={
                "success": True,
                "stdout": "d = 0.72",
                "stderr": "",
                "artifacts": [
                    {
                        "artifact_type": "script",
                        "description": "analysis.py",
                    },
                ],
            },
        )

        grouped = await service.get_linked_artifacts_by_section(manuscript_id)
        assert isinstance(grouped, dict)
        assert len(grouped) > 0

        # Should have at least methods (script) and results (stdout, success)
        for section, links in grouped.items():
            assert isinstance(links, list)
            assert len(links) > 0
            for link in links:
                assert link["section"] == section
                assert link["manuscript_id"] == manuscript_id

    @pytest.mark.asyncio
    async def test_get_artifacts_for_section(self, db_session):
        """Verify section-specific artifact queries."""
        manuscript_id = str(uuid4())

        service = ArtifactLinkingService(db_session)
        await service.build_links(
            manuscript_id=manuscript_id,
            experiment={
                "success": True,
                "stdout": "Accuracy: 0.942",
                "stderr": "",
                "artifacts": [
                    {
                        "artifact_type": "script",
                        "description": "analysis.py",
                    },
                ],
            },
        )

        results_artifacts = await service.get_artifacts_for_section(
            manuscript_id, "results"
        )
        assert len(results_artifacts) > 0
        for art in results_artifacts:
            assert art["section"] == "results"

        methods_artifacts = await service.get_artifacts_for_section(
            manuscript_id, "methods"
        )
        assert len(methods_artifacts) > 0
        for art in methods_artifacts:
            assert art["section"] == "methods"

    @pytest.mark.asyncio
    async def test_build_links_no_data(self, db_session):
        """Verify building links with no data produces zero links."""
        manuscript_id = str(uuid4())
        service = ArtifactLinkingService(db_session)

        result = await service.build_links(
            manuscript_id=manuscript_id,
            experiment=None,
            claims=None,
            effect_sizes=None,
        )

        assert result.links_created == 0
        assert result.sections_with_links == []
        assert result.artifact_types_linked == []

    @pytest.mark.asyncio
    async def test_build_links_error_claim_in_discussion(self, db_session):
        """Verify error-type claims are linked to the discussion section."""
        manuscript_id = str(uuid4())

        service = ArtifactLinkingService(db_session)
        result = await service.build_links(
            manuscript_id=manuscript_id,
            claims=[
                {
                    "statement": "Experiment failed with timeout",
                    "claim_type": "error",
                    "confidence": 0.9,
                    "evidence": "RuntimeError: timeout",
                },
            ],
        )

        assert result.links_created > 0

        links = await service.get_links_for_manuscript(
            manuscript_id, artifact_type="claim"
        )
        assert len(links) > 0
        # Error claims should go to discussion
        discussion_links = [l for l in links if l["section"] == "discussion"]
        assert len(discussion_links) > 0

    @pytest.mark.asyncio
    async def test_build_links_large_effect_size_in_discussion(self, db_session):
        """Verify large effect sizes are linked to both results and discussion."""
        manuscript_id = str(uuid4())

        service = ArtifactLinkingService(db_session)
        result = await service.build_links(
            manuscript_id=manuscript_id,
            effect_sizes=[
                {
                    "effect_type": "cohens_d",
                    "value": 1.5,
                    "label": "Cohen's d",
                    "interpretation": "large",
                    "evidence": "d = 1.5",
                },
            ],
        )

        assert result.links_created > 0

        links = await service.get_links_for_manuscript(
            manuscript_id, artifact_type="effect_size"
        )
        assert len(links) > 0

        sections = {l["section"] for l in links}
        assert "results" in sections
        assert "discussion" in sections

    @pytest.mark.asyncio
    async def test_import_error_claim_to_discussion(self, db_session):
        """Verify error claims map to discussion section."""
        manuscript_id = str(uuid4())

        service = ArtifactLinkingService(db_session)
        await service.build_links(
            manuscript_id=manuscript_id,
            claims=[
                {
                    "statement": "ModuleNotFoundError: No module named 'numpy'",
                    "claim_type": "error",
                    "confidence": 0.95,
                    "evidence": "Import error during execution",
                },
            ],
        )

        links = await service.get_links_for_manuscript(manuscript_id)
        discussion_links = [l for l in links if l["section"] == "discussion"]
        assert len(discussion_links) > 0
