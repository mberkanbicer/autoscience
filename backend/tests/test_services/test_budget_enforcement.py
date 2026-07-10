"""Tests for budget hard-cap enforcement: is_budget_exceeded, _execute_step,
budget_extension_approved flag, and orchestrator resume logic."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.schemas.research_state import ResearchState, RunState, RunType, RunBudget
from app.workflows.research_workflow import (
    ResearchWorkflow,
    WorkflowConfig,
    WorkflowStep,
    WorkflowStatus,
)
from app.workflows.safety_gates import ApprovalGateError, ProjectSafetySettings
from app.services.orchestrator import ResearchOrchestrator


# ---------------------------------------------------------------------------
# ResearchState.is_budget_exceeded tests
# ---------------------------------------------------------------------------


def make_state(
    cost_usd: float = 0.0,
    minutes_elapsed: float = 0.0,
    sources_searched: int = 0,
    max_cost_usd: float = 5.0,
    max_minutes: int = 60,
    max_sources: int = 50,
    budget_extension_approved: bool = False,
) -> ResearchState:
    """Helper to create a ResearchState with the given budget parameters."""
    return ResearchState(
        run_id=str(uuid4()),
        project_id=str(uuid4()),
        run_type=RunType.USER_DIRECTED,
        cost_usd=cost_usd,
        minutes_elapsed=minutes_elapsed,
        sources_searched=sources_searched,
        budget=RunBudget(
            max_cost_usd=max_cost_usd,
            max_minutes=max_minutes,
            max_sources=max_sources,
        ),
        budget_extension_approved=budget_extension_approved,
    )


class TestIsBudgetExceeded:
    """Tests for ResearchState.is_budget_exceeded()."""

    def test_not_exceeded_when_all_within_limits(self):
        """All budget dimensions under their limits."""
        state = make_state(
            cost_usd=1.0,
            minutes_elapsed=10,
            sources_searched=5,
            max_cost_usd=5.0,
            max_minutes=60,
            max_sources=50,
        )
        assert state.is_budget_exceeded() is False

    def test_exceeded_when_cost_at_limit(self):
        """cost_usd == max_cost_usd should be exceeded."""
        state = make_state(
            cost_usd=5.0,
            minutes_elapsed=10,
            sources_searched=5,
            max_cost_usd=5.0,
        )
        assert state.is_budget_exceeded() is True

    def test_exceeded_when_cost_over_limit(self):
        """cost_usd > max_cost_usd should be exceeded."""
        state = make_state(
            cost_usd=7.5,
            minutes_elapsed=10,
            sources_searched=5,
            max_cost_usd=5.0,
        )
        assert state.is_budget_exceeded() is True

    def test_exceeded_when_minutes_at_limit(self):
        """minutes_elapsed == max_minutes should be exceeded."""
        state = make_state(
            cost_usd=1.0,
            minutes_elapsed=60,
            sources_searched=5,
            max_minutes=60,
        )
        assert state.is_budget_exceeded() is True

    def test_exceeded_when_minutes_over_limit(self):
        """minutes_elapsed > max_minutes should be exceeded."""
        state = make_state(
            cost_usd=1.0,
            minutes_elapsed=120,
            sources_searched=5,
            max_minutes=60,
        )
        assert state.is_budget_exceeded() is True

    def test_exceeded_when_sources_at_limit(self):
        """sources_searched == max_sources should be exceeded."""
        state = make_state(
            cost_usd=1.0,
            minutes_elapsed=10,
            sources_searched=50,
            max_sources=50,
        )
        assert state.is_budget_exceeded() is True

    def test_exceeded_when_sources_over_limit(self):
        """sources_searched > max_sources should be exceeded."""
        state = make_state(
            cost_usd=1.0,
            minutes_elapsed=10,
            sources_searched=100,
            max_sources=50,
        )
        assert state.is_budget_exceeded() is True

    def test_exceeded_when_all_over_limits(self):
        """All dimensions over their limits should still be exceeded."""
        state = make_state(
            cost_usd=10.0,
            minutes_elapsed=120,
            sources_searched=100,
            max_cost_usd=5.0,
            max_minutes=60,
            max_sources=50,
        )
        assert state.is_budget_exceeded() is True


class TestBudgetRemaining:
    """Tests for ResearchState.budget_remaining()."""

    def test_full_budget(self):
        """All budget remaining at the start of a run."""
        state = make_state()
        remaining = state.budget_remaining()
        assert remaining["minutes"] == pytest.approx(1.0)
        assert remaining["sources"] == pytest.approx(1.0)
        assert remaining["cost"] == pytest.approx(1.0)

    def test_partial_usage(self):
        """50% used across all dimensions."""
        state = make_state(
            cost_usd=2.5,
            minutes_elapsed=30,
            sources_searched=25,
            max_cost_usd=5.0,
            max_minutes=60,
            max_sources=50,
        )
        remaining = state.budget_remaining()
        assert remaining["minutes"] == pytest.approx(0.5)
        assert remaining["sources"] == pytest.approx(0.5)
        assert remaining["cost"] == pytest.approx(0.5)

    def test_exceeded_returns_zero(self):
        """Budget exceeded returns 0 remaining, not negative."""
        state = make_state(
            cost_usd=10.0,
            minutes_elapsed=120,
            sources_searched=100,
            max_cost_usd=5.0,
            max_minutes=60,
            max_sources=50,
        )
        remaining = state.budget_remaining()
        assert remaining["minutes"] == 0
        assert remaining["sources"] == 0
        assert remaining["cost"] == 0


# ---------------------------------------------------------------------------
# ResearchWorkflow._execute_step budget enforcement tests
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_workflow():
    """Create a ResearchWorkflow with mocked dependencies for step testing."""
    workflow = ResearchWorkflow.__new__(ResearchWorkflow)
    workflow.agents = {}
    workflow.config = WorkflowConfig(run_type="user_directed")
    workflow.step_history = []
    workflow.status = WorkflowStatus.PENDING
    workflow.run_id = str(uuid4())
    workflow.run_service = None
    workflow.safety_service = None
    workflow.project_safety_settings = ProjectSafetySettings()
    workflow.keyword_engine = None
    workflow.literature_engine = None
    workflow.analysis_engine = None
    workflow.clustering_engine = None
    workflow.conflict_engine = None
    workflow.question_engine = None
    workflow.hypothesis_engine = None
    workflow.validation_engine = None
    workflow.scoring_engine = None
    workflow.idea_ledger = None
    workflow.db = None
    workflow.event_broadcaster = None
    workflow.knowledge_service = None

    # Mock _broadcast_event to be a no-op
    workflow._broadcast_event = AsyncMock()

    return workflow


async def _noop_handler(state):
    """A handler that returns state unchanged."""
    return state


class TestExecuteStepBudgetEnforcement:
    """Tests for the budget hard-cap check in _execute_step."""

    async def test_executes_when_budget_not_exceeded(self, mock_workflow):
        """Normal step execution proceeds when budget is fine."""
        state = make_state(
            cost_usd=2.0,
            minutes_elapsed=20,
            sources_searched=10,
            max_cost_usd=5.0,
            max_minutes=60,
            max_sources=50,
        )
        result = await mock_workflow._execute_step(
            state,
            WorkflowStep.ANALYZE_PAPERS,
            _noop_handler,
        )
        # Should complete without raising
        assert result is state
        # _execute_step sets current_phase = step.value before calling handler,
        # and _noop_handler doesn't change it, so it stays as the step value
        assert result.current_phase == "analyze_papers"

    async def test_raises_approval_when_cost_exceeded(self, mock_workflow):
        """Cost exceeding max_cost_usd should raise ApprovalGateError."""
        # Mock safety_service.request_approval to return a mock approval
        mock_approval = MagicMock()
        mock_approval.id = "approval-budget-001"
        mock_workflow.safety_service = MagicMock()
        mock_workflow.safety_service.request_approval = AsyncMock(
            return_value=mock_approval
        )

        state = make_state(
            cost_usd=5.0,
            minutes_elapsed=10,
            sources_searched=5,
            max_cost_usd=5.0,
        )

        with pytest.raises(ApprovalGateError) as exc_info:
            await mock_workflow._execute_step(
                state,
                WorkflowStep.ANALYZE_PAPERS,
                _noop_handler,
            )

        assert exc_info.value.approval_id == "approval-budget-001"
        assert "budget" in exc_info.value.message.lower()
        assert "exhausted" in exc_info.value.message.lower()
        mock_workflow.safety_service.request_approval.assert_awaited_once_with(
            project_id=state.project_id,
            run_id=mock_workflow.run_id,
            action_type="budget_extension",
            action_description=exc_info.value.message,
            action_payload={
                "step": "analyze_papers",
                "cost_usd": 5.0,
                "max_cost_usd": 5.0,
                "budget_remaining": state.budget_remaining(),
            },
        )

    async def test_raises_approval_when_minutes_exceeded(self, mock_workflow):
        """Minutes exceeding max_minutes should raise ApprovalGateError."""
        mock_approval = MagicMock()
        mock_approval.id = "approval-budget-002"
        mock_workflow.safety_service = MagicMock()
        mock_workflow.safety_service.request_approval = AsyncMock(
            return_value=mock_approval
        )

        state = make_state(
            cost_usd=1.0,
            minutes_elapsed=60,
            sources_searched=5,
            max_minutes=60,
        )

        with pytest.raises(ApprovalGateError) as exc_info:
            await mock_workflow._execute_step(
                state,
                WorkflowStep.GENERATE_QUESTIONS,
                _noop_handler,
            )

        assert exc_info.value.approval_id == "approval-budget-002"
        mock_workflow.safety_service.request_approval.assert_awaited_once()

    async def test_raises_approval_when_sources_exceeded(self, mock_workflow):
        """Sources exceeding max_sources should raise ApprovalGateError."""
        mock_approval = MagicMock()
        mock_approval.id = "approval-budget-003"
        mock_workflow.safety_service = MagicMock()
        mock_workflow.safety_service.request_approval = AsyncMock(
            return_value=mock_approval
        )

        state = make_state(
            cost_usd=1.0,
            minutes_elapsed=10,
            sources_searched=50,
            max_sources=50,
        )

        with pytest.raises(ApprovalGateError) as exc_info:
            await mock_workflow._execute_step(
                state,
                WorkflowStep.CLUSTER_PAPERS,
                _noop_handler,
            )

        assert exc_info.value.approval_id == "approval-budget-003"
        mock_workflow.safety_service.request_approval.assert_awaited_once()

    async def test_skips_budget_check_when_extension_approved(self, mock_workflow):
        """When budget_extension_approved is True, the budget check is skipped."""
        mock_workflow.safety_service = MagicMock()
        mock_workflow.safety_service.request_approval = AsyncMock()

        state = make_state(
            cost_usd=10.0,
            minutes_elapsed=10,
            sources_searched=5,
            max_cost_usd=5.0,
            budget_extension_approved=True,
        )

        # Should NOT raise ApprovalGateError because budget_extension_approved=True
        result = await mock_workflow._execute_step(
            state,
            WorkflowStep.SCORE_IDEA,
            _noop_handler,
        )

        assert result is state
        # The approval request should NOT have been called
        mock_workflow.safety_service.request_approval.assert_not_awaited()

    async def test_does_not_call_safety_service_when_missing(self, mock_workflow):
        """When safety_service is None, the budget check logs and continues gracefully."""
        mock_workflow.safety_service = None

        state = make_state(
            cost_usd=10.0,
            minutes_elapsed=10,
            sources_searched=5,
            max_cost_usd=5.0,
        )

        # Budget check fires (logs + broadcasts) but since there's no safety_service
        # to create an approval request, no ApprovalGateError is raised.
        # The step should complete normally (the check is a soft warning).
        result = await mock_workflow._execute_step(
            state,
            WorkflowStep.RETRIEVE_LITERATURE,
            _noop_handler,
        )

        assert result is state
        # Verify the warning was broadcast
        mock_workflow._broadcast_event.assert_any_await(
            "budget_exceeded",
            details={"cost_usd": 10.0, "max_cost_usd": 5.0, "minutes_elapsed": 10.0,
                       "max_minutes": 60, "sources_searched": 5, "max_sources": 50,
                       "budget_remaining": state.budget_remaining()},
        )

    async def test_broadcasts_budget_exceeded_event(self, mock_workflow):
        """The 'budget_exceeded' event should be broadcast when budget is exceeded."""
        mock_approval = MagicMock()
        mock_approval.id = "approval-broadcast-test"
        mock_workflow.safety_service = MagicMock()
        mock_workflow.safety_service.request_approval = AsyncMock(
            return_value=mock_approval
        )

        state = make_state(
            cost_usd=7.5,
            minutes_elapsed=10,
            sources_searched=5,
            max_cost_usd=5.0,
        )

        with pytest.raises(ApprovalGateError):
            await mock_workflow._execute_step(
                state,
                WorkflowStep.RETRIEVE_LITERATURE,
                _noop_handler,
            )

        # Verify the broadcast was called with the right event type
        mock_workflow._broadcast_event.assert_any_await(
            "budget_exceeded",
            details={
                "cost_usd": 7.5,
                "max_cost_usd": 5.0,
                "minutes_elapsed": 10.0,
                "max_minutes": 60,
                "sources_searched": 5,
                "max_sources": 50,
                "budget_remaining": state.budget_remaining(),
            },
        )

    async def test_error_message_includes_all_limits(self, mock_workflow):
        """The ApprovalGateError message should include cost, minutes, and sources info."""
        mock_approval = MagicMock()
        mock_approval.id = "approval-msg-test"
        mock_workflow.safety_service = MagicMock()
        mock_workflow.safety_service.request_approval = AsyncMock(
            return_value=mock_approval
        )

        state = make_state(
            cost_usd=5.0,
            minutes_elapsed=60,
            sources_searched=50,
            max_cost_usd=5.0,
            max_minutes=60,
            max_sources=50,
        )

        with pytest.raises(ApprovalGateError) as exc_info:
            await mock_workflow._execute_step(
                state,
                WorkflowStep.FORM_HYPOTHESES,
                _noop_handler,
            )

        msg = exc_info.value.message
        assert "$5.00" in msg
        assert "60 min" in msg
        assert "50/50" in msg or "50 sources" in msg


    def test_exceeded_with_zero_limits(self):
        """Zero budget limits means budget is always exceeded."""
        state = make_state(
            cost_usd=0.01,
            minutes_elapsed=0.1,
            sources_searched=1,
            max_cost_usd=0.0,  # Zero cost limit
            max_minutes=0,      # Zero minute limit
            max_sources=0,      # Zero source limit
        )
        # Any positive usage exceeds zero limits
        assert state.is_budget_exceeded() is True

    def test_budget_remaining_with_zero_max_returns_zero(self):
        """budget_remaining() with zero max limits returns 0 (no division-by-zero)."""
        state = make_state(
            cost_usd=0.0,
            minutes_elapsed=0.0,
            sources_searched=0,
            max_cost_usd=0.0,
            max_minutes=0,
            max_sources=0,
        )
        remaining = state.budget_remaining()
        # When max is 0, we expect 0 remaining (not NaN from 0/0)
        assert remaining["minutes"] == 0
        assert remaining["sources"] == 0
        assert remaining["cost"] == 0


# ---------------------------------------------------------------------------
# Orchestrator resume logic tests
# ---------------------------------------------------------------------------


class TestOrchestratorResumeBudgetExtension:
    """Tests for the orchestrator's resume_research budget extension logic."""

    async def test_sets_budget_extension_approved_on_resume(self):
        """When resuming a run that exceeded budget, budget_extension_approved should be True.

        This tests the in-line logic used by orchestrator.resume_research():
        if state.is_budget_exceeded(): state.budget_extension_approved = True
        """
        state = make_state(
            cost_usd=10.0,
            minutes_elapsed=10,
            sources_searched=5,
            max_cost_usd=5.0,
        )
        state.state = RunState.WAITING_FOR_APPROVAL

        # Assert the state is marked as budget-exceeded
        assert state.is_budget_exceeded() is True
        assert state.budget_extension_approved is False

        # Simulate what the orchestrator does on resume
        if state.is_budget_exceeded():
            state.budget_extension_approved = True

        # After the logic, the flag should be set
        assert state.budget_extension_approved is True

    async def test_does_not_set_flag_when_budget_not_exceeded(self):
        """When resuming a run that is within budget, budget_extension_approved stays False."""
        state = make_state(
            cost_usd=2.0,
            minutes_elapsed=10,
            sources_searched=5,
            max_cost_usd=5.0,
        )
        state.state = RunState.WAITING_FOR_APPROVAL

        # Should not set the flag since budget is NOT exceeded
        assert state.is_budget_exceeded() is False

        if state.is_budget_exceeded():
            state.budget_extension_approved = True

        assert state.budget_extension_approved is False

    async def test_flag_allows_execution_after_resume(self, mock_workflow):
        """After resume sets budget_extension_approved, step execution should proceed."""
        mock_workflow.safety_service = MagicMock()
        mock_workflow.safety_service.request_approval = AsyncMock()

        state = make_state(
            cost_usd=10.0,
            minutes_elapsed=10,
            sources_searched=5,
            max_cost_usd=5.0,
            budget_extension_approved=True,  # Set by orchestrator resume logic
        )

        # Should NOT raise since flag is True
        result = await mock_workflow._execute_step(
            state,
            WorkflowStep.SCORE_IDEA,
            _noop_handler,
        )

        assert result is state
        mock_workflow.safety_service.request_approval.assert_not_awaited()

    async def test_budget_exceeded_and_not_approved_fails_again_on_resume(self, mock_workflow):
        """If resume does NOT set the flag, the check should fail again."""
        mock_approval = MagicMock()
        mock_approval.id = "approval-recheck"
        mock_workflow.safety_service = MagicMock()
        mock_workflow.safety_service.request_approval = AsyncMock(
            return_value=mock_approval
        )

        state = make_state(
            cost_usd=10.0,
            minutes_elapsed=10,
            sources_searched=5,
            max_cost_usd=5.0,
            budget_extension_approved=False,  # Orchestrator forgot to set this
        )

        with pytest.raises(ApprovalGateError):
            await mock_workflow._execute_step(
                state,
                WorkflowStep.ANALYZE_PAPERS,
                _noop_handler,
            )

        # A new approval should be requested
        mock_workflow.safety_service.request_approval.assert_awaited_once()
