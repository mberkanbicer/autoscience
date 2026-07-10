"""Tests for the research workflow."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from app.workflows.research_workflow import (
    ResearchWorkflow,
    WorkflowConfig,
    WorkflowStep,
    WorkflowStatus,
    WorkflowStepResult,
    _extract_python_code,
    _fallback_experiment_code,
    serialize_step_history,
    deserialize_step_history,
)
from app.sandbox.executor import SandboxResult  # noqa: F401 — direct import avoids package __init__ side effects
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


def test_extract_python_code_from_fence():
    text = "Here is the script:\n```python\nprint('ok')\n```"
    assert _extract_python_code(text) == "print('ok')"


def test_fallback_experiment_code_is_stdlib_only():
    code = _fallback_experiment_code("Graph neural networks improve link prediction")
    assert "import json" in code
    assert "numpy" not in code


@pytest.mark.asyncio
async def test_generate_experiment_stores_code(workflow, state):
    state.hypotheses.append(HypothesisSummary(
        id="h1", statement="Attention sparsity improves efficiency", confidence=0.7, status="draft",
    ))
    result = await workflow._generate_experiment(state)
    assert result.experiment_code
    assert len(result.experiment_code) > 0


@pytest.mark.asyncio
async def test_run_experiment_uses_generated_code(workflow, state):
    from unittest.mock import AsyncMock, patch

    state.experiment_code = "print('unit-test-stdout')"
    mock_result = SandboxResult(
        success=True,
        stdout="unit-test-stdout\n",
        stderr="",
        exit_code=0,
        duration_ms=12,
    )

    mock_executor = AsyncMock()
    mock_executor.run_python = AsyncMock(return_value=mock_result)

    with patch(
        "app.sandbox.executor.SandboxExecutor",
        return_value=mock_executor,
    ):
        result = await workflow._run_experiment(state)

    assert result.experiment_result is not None
    assert result.experiment_result["success"] is True
    assert "unit-test-stdout" in result.experiment_result["stdout"]


def test_step_mapping():
    """Verify all steps have agent mappings."""
    wf = ResearchWorkflow(agents={})
    for step in WorkflowStep:
        if step == WorkflowStep.INITIALIZE:
            continue
        agent = wf._step_to_agent(step)
        assert agent is not None, f"No agent mapping for {step}"


def test_serialize_step_history():
    history = [
        WorkflowStepResult(step=WorkflowStep.PLAN_SEARCH, status="completed", duration_seconds=1.5),
        WorkflowStepResult(step=WorkflowStep.SCORE_IDEA, status="failed", duration_seconds=0.2, error="boom"),
    ]
    serialized = serialize_step_history(history)
    assert serialized[0]["step"] == "plan_search"
    assert serialized[0]["status"] == "completed"
    assert serialized[1]["error"] == "boom"


def test_deserialize_step_history_round_trip():
    history = [
        WorkflowStepResult(
            step=WorkflowStep.PLAN_SEARCH,
            status="completed",
            duration_seconds=1.5,
            output={"keywords": 3},
        ),
        WorkflowStepResult(
            step=WorkflowStep.SCORE_IDEA,
            status="failed",
            duration_seconds=0.2,
            error="boom",
        ),
    ]
    restored = deserialize_step_history(serialize_step_history(history))
    assert len(restored) == 2
    assert restored[0].step == WorkflowStep.PLAN_SEARCH
    assert restored[0].output == {"keywords": 3}
    assert restored[1].error == "boom"


@pytest.mark.asyncio
async def test_persist_step_history_calls_run_service():
    run_service = AsyncMock()
    workflow = ResearchWorkflow(
        agents={},
        config=WorkflowConfig(run_type="user_directed"),
        run_id="run-123",
        run_service=run_service,
    )
    workflow.step_history.append(
        WorkflowStepResult(step=WorkflowStep.PLAN_SEARCH, status="completed", duration_seconds=2.0)
    )

    await workflow._persist_step_history()

    run_service.update_step_history.assert_awaited_once()
    args = run_service.update_step_history.await_args[0]
    assert args[0] == "run-123"
    assert args[1][0]["step"] == "plan_search"
