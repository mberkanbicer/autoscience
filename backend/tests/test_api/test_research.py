"""Tests for research API and orchestrator idea lifecycle."""

from unittest.mock import AsyncMock, patch  # noqa: F401 — patch used in multiple tests
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idea import Idea
from app.models.research_run import ResearchRun
from app.schemas.research_state import ResearchState, RunBudget, RunState, RunType
from app.services.idea_ledger_service import IdeaLedgerService
from app.services.orchestrator import ResearchOrchestrator
from app.services.research_run_service import ResearchRunService
from app.schemas.research_run import ResearchRunCreate


@pytest.mark.asyncio
async def test_start_research_creates_single_idea(client: AsyncClient):
    """POST /research/run must not create duplicate ideas when background workflow starts."""
    from unittest.mock import patch

    project_response = await client.post(
        "/api/v1/projects",
        json={"name": "Research Test", "domain": "AI"},
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    with patch("app.api.research.asyncio.create_task"):
        research_response = await client.post(
            "/api/v1/research/run",
            json={
                "project_id": project_id,
                "idea": "Investigate transformer attention sparsity patterns",
                "run_type": "user_directed",
                "flexibility": 0.6,
            },
        )
    assert research_response.status_code == 200
    data = research_response.json()
    assert data["success"] is True
    assert "run_id" in data
    assert "idea_id" in data

    ideas_response = await client.get(f"/api/v1/ideas?project_id={project_id}")
    assert ideas_response.status_code == 200
    ideas = ideas_response.json()
    assert len(ideas) == 1
    assert ideas[0]["id"] == data["idea_id"]


@pytest.mark.asyncio
async def test_run_research_with_existing_run_reuses_idea(db_session: AsyncSession):
    """Orchestrator must reuse the run's idea instead of creating a duplicate."""
    from app.models.project import Project

    project = Project(
        id=str(uuid4()),
        name="Orchestrator Test",
        domain="ML",
        default_flexibility=0.6,
        idle_research_enabled=False,
        idle_trigger_minutes=120,
        max_idle_cycles_per_day=3,
        max_sources_per_cycle=50,
        approval_required_for_external_actions=True,
    )
    db_session.add(project)
    await db_session.flush()

    idea_ledger = IdeaLedgerService(db_session)
    idea = await idea_ledger.create_idea(
        project_id=project.id,
        text="Test hypothesis on graph neural networks",
        origin="user_prompt",
        flexibility=0.6,
    )

    run_service = ResearchRunService(db_session)
    run = await run_service.create_run(
        project_id=project.id,
        data=ResearchRunCreate(idea_id=idea.id, run_type="user_directed"),
    )
    await db_session.commit()

    mock_llm = AsyncMock()
    mock_connectors = AsyncMock()

    completed_state = ResearchState(
        run_id=run.id,
        project_id=project.id,
        idea_id=idea.id,
        run_type=RunType.USER_DIRECTED,
        original_idea=idea.current_text,
        current_idea=idea.current_text,
        flexibility=0.6,
        budget=RunBudget(),
        state=RunState.COMPLETED,
    )

    orchestrator = ResearchOrchestrator(
        db=db_session,
        llm_router=mock_llm,
        connector_manager=mock_connectors,
    )

    with (
        patch.object(ResearchOrchestrator, "_store_results", new_callable=AsyncMock),
        patch(
            "app.services.orchestrator.ResearchWorkflow.run",
            new_callable=AsyncMock,
            return_value=completed_state,
        ),
        patch.object(orchestrator.report_generator, "generate_report", new_callable=AsyncMock, return_value="report"),
        patch.object(orchestrator.report_generator, "save_report", new_callable=AsyncMock),
        patch.object(orchestrator.knowledge_service, "generate_project_summary", new_callable=AsyncMock),
        patch.object(orchestrator.audit_service, "log_event", new_callable=AsyncMock),
    ):
        await orchestrator.run_research(
            project_id=project.id,
            idea_text=idea.current_text,
            run_type="user_directed",
            flexibility=0.6,
            existing_run_id=run.id,
        )

    count_result = await db_session.execute(
        select(func.count(Idea.id)).where(Idea.project_id == project.id)
    )
    assert count_result.scalar() == 1

    run_result = await db_session.execute(
        select(ResearchRun).where(ResearchRun.id == run.id)
    )
    persisted_run = run_result.scalar_one()
    assert persisted_run.idea_id == idea.id


@pytest.mark.asyncio
async def test_store_results_persists_full_score_dimensions(db_session: AsyncSession):
    """_store_results should persist all scoring dimensions, not only overall_value."""
    from app.models.idea import Idea, IdeaScore
    from app.models.project import Project
    from app.schemas.research_state import ResearchState, RunBudget, RunType, ScoreSummary
    from unittest.mock import AsyncMock

    project = Project(
        id=str(uuid4()),
        name="Score Test",
        domain="ML",
        default_flexibility=0.6,
        idle_research_enabled=False,
        idle_trigger_minutes=120,
        max_idle_cycles_per_day=3,
        max_sources_per_cycle=50,
        approval_required_for_external_actions=True,
    )
    db_session.add(project)
    await db_session.flush()

    idea = Idea(
        id=str(uuid4()),
        project_id=project.id,
        origin="user_prompt",
        initial_text="Score persistence test",
        current_text="Score persistence test",
        status="active",
    )
    db_session.add(idea)
    await db_session.flush()

    state = ResearchState(
        run_id=str(uuid4()),
        project_id=project.id,
        idea_id=idea.id,
        run_type=RunType.USER_DIRECTED,
        original_idea=idea.current_text,
        current_idea=idea.current_text,
        flexibility=0.6,
        budget=RunBudget(),
        scores=[
            ScoreSummary(
                id="score-1",
                novelty=8.0,
                feasibility=7.0,
                importance=9.0,
                evidence_support=6.5,
                validation_clarity=7.5,
                differentiation=8.0,
                data_availability=6.0,
                skill_leverage=5.0,
                user_alignment=8.5,
                prior_art_risk=3.0,
                safety_risk=2.0,
                cost_risk=4.0,
                overall_value=7.8,
                classification="promising",
                rationale="Strong novelty with manageable risk.",
            )
        ],
    )

    orchestrator = ResearchOrchestrator(
        db=db_session,
        llm_router=AsyncMock(),
        connector_manager=AsyncMock(),
    )
    with patch(
        "app.services.research_persistence_service.EmbeddingService.embed_papers_batch",
        new=AsyncMock(return_value=0),
    ):
        await orchestrator._store_results(state)
    await db_session.commit()

    result = await db_session.execute(
        select(IdeaScore).where(IdeaScore.idea_id == idea.id)
    )
    stored = result.scalar_one()
    assert stored.novelty == 8.0
    assert stored.feasibility == 7.0
    assert stored.importance == 9.0
    assert stored.overall_value == 7.8
    assert "Strong novelty" in (stored.scoring_rationale or "")