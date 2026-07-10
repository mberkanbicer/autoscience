"""Tests for unified research persistence."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models.idea import Idea
from app.models.paper import Paper
from app.models.project import Project
from app.schemas.research_state import PaperSummary, ResearchState, RunBudget, RunType
from app.services.research_persistence_service import ResearchPersistenceService


@pytest.mark.asyncio
async def test_persist_papers_batch_dedup_and_db_dedup(db_session):
    project_id = str(uuid4())
    db_session.add(
        Project(
            id=project_id,
            name="Persistence Test",
            domain="ML",
            default_flexibility=0.6,
            idle_research_enabled=False,
            idle_trigger_minutes=120,
            max_idle_cycles_per_day=3,
            max_sources_per_cycle=50,
            approval_required_for_external_actions=True,
        )
    )
    existing_paper_id = str(uuid4())
    db_session.add(
        Paper(
            id=existing_paper_id,
            project_id=project_id,
            title="Attention Is All You Need",
            authors=["Vaswani"],
            year=2017,
            doi="10.5555/3295222.3295349",
        )
    )
    await db_session.flush()

    state = ResearchState(
        run_id=str(uuid4()),
        project_id=project_id,
        run_type=RunType.USER_DIRECTED,
        original_idea="Transformers",
        current_idea="Transformers",
        budget=RunBudget(),
        papers=[
            PaperSummary(
                id="state-1",
                title="Attention Is All You Need",
                authors=["Vaswani"],
                year=2017,
                doi="10.5555/3295222.3295349",
            ),
            PaperSummary(
                id="state-2",
                title="Attention Is All You Need",
                authors=["Vaswani et al."],
                year=2017,
                doi="10.5555/3295222.3295349",
            ),
            PaperSummary(
                id="state-3",
                title="BERT: Pre-training of Deep Bidirectional Transformers",
                authors=["Devlin"],
                year=2019,
            ),
        ],
    )

    service = ResearchPersistenceService(db_session, llm_router=None)
    with patch.object(service.embedding_service, "embed_papers_batch", new=AsyncMock(return_value=0)):
        result = await service.persist_run_results(state)

    assert result.stored["papers"] == 1
    assert result.skipped["papers"] == 1
    assert result.paper_id_map["state-1"] == existing_paper_id
    assert result.paper_id_map["state-2"] == existing_paper_id
    assert result.paper_id_map["state-3"] != existing_paper_id


def test_cosine_similarity():
    from app.services.embedding_service import cosine_similarity

    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)