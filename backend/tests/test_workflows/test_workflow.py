"""Tests for the research workflow."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from app.workflows.research_workflow import (
    ResearchWorkflow,
    WorkflowConfig,
    WorkflowStep,
    WorkflowStatus,
)
from app.schemas.research_state import ResearchState, RunState, RunType, RunBudget
from app.schemas.research_state import ConflictSummary, QuestionSummary, HypothesisSummary, ClusterSummary, ScoreSummary, PaperSummary


@pytest.fixture
def workflow():
    return ResearchWorkflow(
        agents={},
        config=WorkflowConfig(run_type="user_directed"),
        run_id="test-run-1",
    )


@pytest.fixture
def state():
    return ResearchState(
        run_id="test-run-1",
        project_id="test-project",
        idea_id="test-idea",
        original_idea="Test research idea",
        current_idea="Test research idea",
        flexibility=0.6,
        budget=RunBudget(),
        run_type=RunType.USER_DIRECTED,
    )


@pytest.mark.asyncio
async def test_workflow_init(workflow):
    assert workflow.status == WorkflowStatus.PENDING
    assert workflow.run_id == "test-run-1"
    assert len(workflow.step_history) == 0


def test_workflow_pause_resume(workflow):
    workflow.pause()
    assert workflow.status == WorkflowStatus.PAUSED
    workflow.resume()
    assert workflow.status == WorkflowStatus.RUNNING


def test_workflow_cancel(workflow):
    workflow.cancel()
    assert workflow.status == WorkflowStatus.CANCELLED


@pytest.mark.asyncio
async def test_interpret_intent_no_agents(workflow, state):
    """Without any agents, interpret_intent should not crash."""
    result = await workflow._interpret_intent(state)
    # Without agents, phase stays at default (initialized)
    assert result is not None


@pytest.mark.asyncio
async def test_plan_search_no_keyword_engine(workflow, state):
    result = await workflow._plan_search(state)
    assert result.current_phase == "search_planned"
    assert isinstance(result.keywords, list)


@pytest.mark.asyncio
async def test_wiki_notes_generation_empty(workflow, state):
    """Verify _generate_wiki_notes handles empty state gracefully."""
    await workflow._generate_wiki_notes(state)
    # Should not raise even with no data


@pytest.mark.asyncio
async def test_wiki_notes_with_data(workflow, state):
    """Generate notes from populated state."""
    state.papers.append(PaperSummary(
        id="p1", title="Test Paper", authors=["Author1"], year=2024,
    ))
    state.clusters.append(ClusterSummary(
        id="c1", name="Test Cluster", description="A test", paper_count=3,
    ))
    state.conflicts.append(ConflictSummary(
        id="conf1", conflict_type="methodological", description="A conflict", severity=0.5,
    ))
    state.hypotheses.append(HypothesisSummary(
        id="h1", statement="Test hypothesis", confidence=0.7, status="draft",
    ))
    await workflow._generate_wiki_notes(state)
    # Should not raise


def test_phase_labels(workflow):
    """Verify all workflow steps have phase labels."""
    for step in WorkflowStep:
        label = workflow._phase_label(step)
        assert label and len(label) > 0


@pytest.mark.asyncio
async def test_user_directed_execution(workflow, state):
    """Full workflow execution with default (empty) config should not crash."""
    # Skip — full execution requires all engines/agents wired
    pytest.skip("Full execution test needs engines wired")


def test_step_mapping():
    """Verify all steps have agent mappings."""
    wf = ResearchWorkflow(agents={})
    for step in WorkflowStep:
        if step == WorkflowStep.INITIALIZE:
            continue
        agent = wf._step_to_agent(step)
        assert agent is not None, f"No agent mapping for {step}"
