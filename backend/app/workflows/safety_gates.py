"""Safety gate helpers for workflow step enforcement."""

from dataclasses import dataclass

from app.services.safety_service import ActionType, PermissionLevel, SafetyService

# Estimated incremental LLM/API cost per gated step (USD)
STEP_COST_ESTIMATES: dict[str, float] = {
    "retrieve_literature": 0.75,
    "run_experiment": 0.35,
    "generate_manuscript": 1.25,
}

# Steps that require budget/approval checks before execution
GATED_STEPS: set[str] = set(STEP_COST_ESTIMATES.keys())

# DESIGN.md: mandatory gate when projected spend exceeds this threshold
SPEND_APPROVAL_THRESHOLD_USD = 1.0


class ApprovalGateError(Exception):
    """Raised when a workflow step requires user approval before continuing."""

    def __init__(self, approval_id: str, step: str, message: str):
        self.approval_id = approval_id
        self.step = step
        self.message = message
        super().__init__(message)


@dataclass
class ProjectSafetySettings:
    """Project-level safety configuration passed into the workflow."""

    approval_required_for_external_actions: bool = True
    max_cost_per_run_usd: float = 5.0


async def enforce_step_safety_gate(
    *,
    safety_service: SafetyService,
    project_id: str,
    run_id: str | None,
    step: str,
    current_cost_usd: float,
    project_settings: ProjectSafetySettings,
) -> None:
    """Block a gated step when budget limits or spend approval thresholds are exceeded."""
    if step not in GATED_STEPS:
        return

    estimated_step_cost = STEP_COST_ESTIMATES.get(step, 0.0)
    projected_cost = current_cost_usd + estimated_step_cost

    permission = safety_service.check_permission(ActionType.SPEND_MONEY, project_id)
    if permission == PermissionLevel.NEVER_ALLOWED:
        raise ApprovalGateError("", step, f"Action blocked: {step} is never allowed")

    budget_ok, budget_reason = safety_service.check_budget(project_id, projected_cost)
    over_spend_threshold = projected_cost > SPEND_APPROVAL_THRESHOLD_USD
    requires_approval = (
        not budget_ok
        or (
            over_spend_threshold
            and project_settings.approval_required_for_external_actions
            and permission == PermissionLevel.APPROVAL_REQUIRED
        )
    )

    if not requires_approval:
        return

    action_type = "spend" if over_spend_threshold else "budget_exceeded"
    description = (
        f"Workflow step '{step}' requires approval. "
        f"Projected cost ${projected_cost:.2f} "
        f"(current ${current_cost_usd:.2f} + step ${estimated_step_cost:.2f}). "
        f"{budget_reason}"
    )

    approval = await safety_service.request_approval(
        project_id=project_id,
        run_id=run_id,
        action_type=action_type,
        action_description=description,
        action_payload={
            "step": step,
            "current_cost_usd": current_cost_usd,
            "estimated_step_cost": estimated_step_cost,
            "projected_cost_usd": projected_cost,
            "budget_reason": budget_reason,
        },
    )

    raise ApprovalGateError(approval.id, step, description)
