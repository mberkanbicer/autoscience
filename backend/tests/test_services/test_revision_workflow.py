"""Tests for the Research→Experiment→Article revision workflow."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.models.report import Manuscript
from app.services.revision_workflow_service import (
    RevisionWorkflowService,
    ManuscriptGap,
    _infer_severity,
)
from app.services.research_run_service import ResearchRunService
from app.services.idea_ledger_service import IdeaLedgerService


class TestManuscriptGap:
    """Tests for the ManuscriptGap dataclass and helpers."""

    def test_manuscript_gap_defaults(self):
        gap = ManuscriptGap(description="Test gap", source="peer_review")
        assert gap.description == "Test gap"
        assert gap.source == "peer_review"
        assert gap.severity == pytest.approx(0.5)

    def test_infer_severity_high(self):
        assert _infer_severity("This is a critical flaw") == 0.9
        assert _infer_severity("Fatal error in methodology") == 0.9

    def test_infer_severity_medium(self):
        assert _infer_severity("Insufficient evidence") == 0.7
        assert _infer_severity("Weak methodology") == 0.7

    def test_infer_severity_default(self):
        assert _infer_severity("Consider alternative approach") == 0.5


class TestGapExtraction:
    """Tests for the gap extraction logic."""

    @pytest.mark.asyncio
    async def test_extract_gaps_from_review(self, db_session):
        """Gaps should be extracted from peer review feedback."""
        manuscript = Manuscript(
            id=str(uuid4()),
            project_id=str(uuid4()),
            title="Test Manuscript",
            status="draft",
            version=1,
        )
        db_session.add(manuscript)
        await db_session.flush()

        # Build a lightweight service
        service = RevisionWorkflowService.__new__(RevisionWorkflowService)
        service.db = db_session
        service.llm = None

        review = {
            "weaknesses": ["Insufficient sample size", "No baseline comparison"],
            "questions": ["How does this generalize to other domains?"],
            "summary": "Needs improvement",
        }

        gaps = await service._extract_gaps(manuscript, review)

        assert len(gaps) >= 3
        gap_descriptions = [g.description for g in gaps]
        assert any("Insufficient sample size" in d for d in gap_descriptions)
        assert any("No baseline comparison" in d for d in gap_descriptions)
        assert any("generalize" in d for d in gap_descriptions)

    @pytest.mark.asyncio
    async def test_extract_gaps_from_manuscript_text(self, db_session):
        """Gaps should be extracted from manuscript limitations section."""
        manuscript = Manuscript(
            id=str(uuid4()),
            project_id=str(uuid4()),
            title="Test with Limitations",
            content_latex=r"\section{Discussion} This study has limitations. Further research is needed to validate these findings across different settings. Some open questions remain about the generalizability.",
            status="draft",
            version=1,
        )
        db_session.add(manuscript)
        await db_session.flush()

        service = RevisionWorkflowService.__new__(RevisionWorkflowService)
        service.db = db_session
        service.llm = None

        gaps = await service._extract_gaps(manuscript, None)

        assert len(gaps) >= 3
        descriptions = [g.description for g in gaps]
        assert any("Further research" in d for d in descriptions)
        assert any("limitation" in d.lower() or "Limitation" in d for d in descriptions)

    @pytest.mark.asyncio
    async def test_default_gap_when_none_found(self, db_session):
        """A default gap should be created when no specific gaps are found."""
        manuscript = Manuscript(
            id=str(uuid4()),
            project_id=str(uuid4()),
            title="Minimal Manuscript",
            content_latex=r"\section{Introduction} Simple intro.",
            status="draft",
            version=1,
        )
        db_session.add(manuscript)
        await db_session.flush()

        service = RevisionWorkflowService.__new__(RevisionWorkflowService)
        service.db = db_session
        service.llm = None

        gaps = await service._extract_gaps(manuscript, None)

        assert len(gaps) >= 1
        assert gaps[0].description is not None


class TestRevisionHistory:
    """Tests for revision lineage tracking."""

    @pytest.mark.asyncio
    async def test_get_revision_history(self, db_session):
        """Revision history should return ancestors and descendants."""
        # Create a chain: ms1 -> ms2 (child) -> ms3 (grandchild)
        ms1 = Manuscript(
            id=str(uuid4()),
            project_id=str(uuid4()),
            title="Original",
            status="finalized",
            version=1,
        )
        db_session.add(ms1)

        ms2 = Manuscript(
            id=str(uuid4()),
            project_id=ms1.project_id,
            title="Revision 1",
            parent_manuscript_id=ms1.id,
            status="draft",
            version=1,
        )
        db_session.add(ms2)

        ms3 = Manuscript(
            id=str(uuid4()),
            project_id=ms1.project_id,
            title="Revision 2",
            parent_manuscript_id=ms2.id,
            status="draft",
            version=1,
        )
        db_session.add(ms3)
        await db_session.flush()

        service = RevisionWorkflowService.__new__(RevisionWorkflowService)
        service.db = db_session
        service.llm = None

        # Get history from ms2
        history = await service.get_revision_history(ms2.id)

        assert len(history) >= 2  # ancestors + descendants
        # Should include ms1 (ancestor) and ms3 (descendant)
        history_ids = [h["manuscript_id"] for h in history]
        assert ms1.id in history_ids
        assert ms3.id in history_ids


class TestCreateRevisionRun:
    """Tests for revision run creation."""

    @pytest.mark.asyncio
    async def test_create_revision_run(self, db_session, sample_project):
        """A revision run should be created linked to manuscript."""
        from sqlalchemy import select
        from app.models.research_run import ResearchRun

        manuscript = Manuscript(
            id=str(uuid4()),
            project_id=sample_project.id,
            title="Test Revision",
            status="draft",
            version=1,
        )
        db_session.add(manuscript)
        await db_session.flush()

        service = RevisionWorkflowService.__new__(RevisionWorkflowService)
        service.db = db_session
        service.run_service = ResearchRunService(db_session)
        service.idea_ledger = IdeaLedgerService(db_session)
        service.llm = None

        run = await service._create_revision_run(
            manuscript=manuscript,
            questions=["Question 1", "Question 2"],
        )

        assert run is not None
        assert run.project_id == sample_project.id
        assert run.run_type == "user_directed"
        assert run.id is not None

    @pytest.mark.asyncio
    async def test_generate_revision_questions_fallback(self, db_session):
        """Without LLM, simple template questions should be generated from gaps."""
        service = RevisionWorkflowService.__new__(RevisionWorkflowService)
        service.db = db_session
        service.llm = None

        manuscript = Manuscript(
            id=str(uuid4()),
            project_id=str(uuid4()),
            title="Test",
            status="draft",
            version=1,
        )

        gaps = [
            ManuscriptGap(description="Weak methodology", source="peer_review"),
            ManuscriptGap(description="Missing baseline", source="peer_review"),
        ]

        questions = await service._generate_revision_questions(manuscript, gaps)
        assert len(questions) == 2
        assert any("Weak methodology" in q for q in questions)
        assert any("Missing baseline" in q for q in questions)
