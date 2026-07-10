"""Tests for workflow safety gates."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.workflows.safety_gates import (
    ApprovalGateError,
    ProjectSafetySettings,
    SPEND_APPROVAL_THRESHOLD_USD,
    enforce_step_safety_gate,
)
from app.services.safety_service import PermissionPolicy, SafetyService


@pytest.mark.asyncio
async def test_enforce_gate_blocks_over_threshold_spend(db_session):
    """Steps over the spend threshold should create an approval request."""
    policy = PermissionPolicy(max_cost_per_run=10.0, max_cost_per_day=50.0)
    safety = SafetyService(db_session, policy=policy)
    safety.request_approval = AsyncMock(
        return_value=MagicMock(id="approval-123")
    )

    project_id = str(uuid4())
    settings = ProjectSafetySettings(approval_required_for_external_actions=True)

    with pytest.raises(ApprovalGateError) as exc_info:
        await enforce_step_safety_gate(
            safety_service=safety,
            project_id=project_id,
            run_id=str(uuid4()),
            step="retrieve_literature",
            current_cost_usd=SPEND_APPROVAL_THRESHOLD_USD,
            project_settings=settings,
        )

    assert exc_info.value.approval_id == "approval-123"
    assert exc_info.value.step == "retrieve_literature"
    safety.request_approval.assert_awaited_once()


@pytest.mark.asyncio
async def test_enforce_gate_allows_low_spend(db_session):
    """Steps below threshold with budget headroom should proceed without approval."""
    policy = PermissionPolicy(max_cost_per_run=10.0, max_cost_per_day=50.0)
    safety = SafetyService(db_session, policy=policy)
    safety.request_approval = AsyncMock()

    await enforce_step_safety_gate(
        safety_service=safety,
        project_id=str(uuid4()),
        run_id=str(uuid4()),
        step="retrieve_literature",
        current_cost_usd=0.0,
        project_settings=ProjectSafetySettings(approval_required_for_external_actions=True),
    )

    safety.request_approval.assert_not_awaited()


@pytest.mark.asyncio
async def test_enforce_gate_skips_non_gated_steps(db_session):
    """Non-gated steps should never trigger approval."""
    safety = SafetyService(db_session)
    safety.request_approval = AsyncMock()

    await enforce_step_safety_gate(
        safety_service=safety,
        project_id=str(uuid4()),
        run_id=str(uuid4()),
        step="analyze_papers",
        current_cost_usd=100.0,
        project_settings=ProjectSafetySettings(),
    )

    safety.request_approval.assert_not_awaited()