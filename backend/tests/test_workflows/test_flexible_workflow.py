"""Tests for flexible workflow configuration."""

from app.schemas.research_state import ResearchState, RunBudget, RunType
from app.workflows.research_workflow import ResearchWorkflow, WorkflowConfig


def _workflow(run_type: str, flexibility: float = 0.6) -> ResearchWorkflow:
    return ResearchWorkflow(
        agents={},
        config=WorkflowConfig(run_type=run_type, flexibility=flexibility),
    )


def test_flexible_mode_expands_literature_limits():
    wf = _workflow("flexible_user", flexibility=0.8)
    state = ResearchState(
        run_id="run-1",
        project_id="proj-1",
        run_type=RunType.FLEXIBLE_USER,
        flexibility=0.8,
        budget=RunBudget(max_sources=50),
    )

    assert wf._literature_limit(state) == 50
    assert wf._literature_year_span() == 10


def test_user_directed_mode_uses_standard_limits():
    wf = _workflow("user_directed", flexibility=0.6)
    state = ResearchState(
        run_id="run-1",
        project_id="proj-1",
        run_type=RunType.USER_DIRECTED,
        flexibility=0.6,
        budget=RunBudget(max_sources=50),
    )

    assert wf._literature_limit(state) == 30
    assert wf._literature_year_span() == 5