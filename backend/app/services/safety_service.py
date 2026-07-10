"""Safety and permissions system for governing autonomous actions."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import ApprovalRequest, AuditLog

logger = structlog.get_logger()


class PermissionLevel(str, Enum):
    """Permission levels for actions."""

    ALWAYS_ALLOWED = "always_allowed"
    APPROVAL_REQUIRED = "approval_required"
    NEVER_ALLOWED = "never_allowed"


class ActionType(str, Enum):
    """Types of actions that require permission."""

    # Always allowed
    SEARCH_ACADEMIC_API = "search_academic_api"
    GENERATE_IDEAS = "generate_ideas"
    WRITE_REPORTS = "write_reports"
    CREATE_SKILLS = "create_skills"
    RUN_SANDBOX_CODE = "run_sandbox_code"

    # Approval required
    SEND_EMAIL = "send_email"
    PUBLISH_CONTENT = "publish_content"
    SUBMIT_PAPER = "submit_paper"
    SPEND_MONEY = "spend_money"
    ACCESS_PRIVATE_ACCOUNTS = "access_private_accounts"
    DOWNLOAD_RESTRICTED = "download_restricted"
    MODIFY_CONFIGURATION = "modify_configuration"
    CHANGE_SAFETY_SETTINGS = "change_safety_settings"

    # Never allowed
    BYPASS_PAYWALLS = "bypass_paywalls"
    SCRAPE_DISALLOWED = "scrape_disallowed"
    FABRICATE_CITATIONS = "fabricate_citations"
    HIDE_FAILED_SEARCHES = "hide_failed_searches"
    DELETE_AUDIT_LOGS = "delete_audit_logs"
    DISABLE_LOGGING = "disable_logging"
    CLAIM_GUARANTEED_NOVELTY = "claim_guaranteed_novelty"


@dataclass
class PermissionPolicy:
    """Policy for action permissions."""

    # Always allowed actions
    always_allowed: list[ActionType] = field(default_factory=lambda: [
        ActionType.SEARCH_ACADEMIC_API,
        ActionType.GENERATE_IDEAS,
        ActionType.WRITE_REPORTS,
        ActionType.CREATE_SKILLS,
        ActionType.RUN_SANDBOX_CODE,
    ])

    # Actions requiring approval
    approval_required: list[ActionType] = field(default_factory=lambda: [
        ActionType.SEND_EMAIL,
        ActionType.PUBLISH_CONTENT,
        ActionType.SUBMIT_PAPER,
        ActionType.SPEND_MONEY,
        ActionType.ACCESS_PRIVATE_ACCOUNTS,
        ActionType.DOWNLOAD_RESTRICTED,
        ActionType.MODIFY_CONFIGURATION,
        ActionType.CHANGE_SAFETY_SETTINGS,
    ])

    # Never allowed actions
    never_allowed: list[ActionType] = field(default_factory=lambda: [
        ActionType.BYPASS_PAYWALLS,
        ActionType.SCRAPE_DISALLOWED,
        ActionType.FABRICATE_CITATIONS,
        ActionType.HIDE_FAILED_SEARCHES,
        ActionType.DELETE_AUDIT_LOGS,
        ActionType.DISABLE_LOGGING,
        ActionType.CLAIM_GUARANTEED_NOVELTY,
    ])

    # Budget limits
    max_cost_per_run: float = 5.0
    max_cost_per_day: float = 20.0
    max_sources_per_run: int = 50

    # Allowed academic sources
    allowed_sources: list[str] = field(default_factory=lambda: [
        "openalex",
        "semantic_scholar",
        "crossref",
        "arxiv",
        "pubmed",
        "doaj",
        "core",
        "unpaywall",
    ])

    # Blocked sources
    blocked_sources: list[str] = field(default_factory=lambda: [
        "google_scholar",  # No scraping allowed
    ])


@dataclass
class ApprovalDecision:
    """Decision on an approval request."""

    request_id: str
    approved: bool
    reason: str | None = None
    decided_by: str = "user"
    decided_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class SafetyService:
    """Service for safety and permission management."""

    def __init__(self, db: AsyncSession, policy: PermissionPolicy | None = None):
        self.db = db
        self.policy = policy or PermissionPolicy()
        self.daily_costs: dict[str, float] = {}  # project_id -> cost today

    def check_permission(
        self,
        action: ActionType,
        project_id: str | None = None,
    ) -> PermissionLevel:
        """Check if an action is allowed."""
        if action in self.policy.never_allowed:
            logger.warning(
                "action_blocked",
                action=action.value,
                reason="Action is never allowed",
            )
            return PermissionLevel.NEVER_ALLOWED

        if action in self.policy.always_allowed:
            return PermissionLevel.ALWAYS_ALLOWED

        if action in self.policy.approval_required:
            return PermissionLevel.APPROVAL_REQUIRED

        # Default: require approval for unknown actions
        return PermissionLevel.APPROVAL_REQUIRED

    def check_source_allowed(self, source: str) -> bool:
        """Check if an academic source is allowed."""
        if source in self.policy.blocked_sources:
            logger.warning("source_blocked", source=source)
            return False

        if source in self.policy.allowed_sources:
            return True

        # Unknown source: require approval
        return False

    def check_budget(
        self,
        project_id: str,
        estimated_cost: float,
    ) -> tuple[bool, str]:
        """Check if action is within budget."""
        # Check per-run budget
        if estimated_cost > self.policy.max_cost_per_run:
            return False, f"Estimated cost ${estimated_cost:.2f} exceeds per-run limit ${self.policy.max_cost_per_run:.2f}"

        # Check daily budget
        today = datetime.now().strftime("%Y-%m-%d")
        daily_key = f"{project_id}:{today}"
        current_daily = self.daily_costs.get(daily_key, 0)

        if current_daily + estimated_cost > self.policy.max_cost_per_day:
            return False, f"Daily budget exceeded. Current: ${current_daily:.2f}, Limit: ${self.policy.max_cost_per_day:.2f}"

        return True, "Budget OK"

    def record_cost(self, project_id: str, cost: float) -> None:
        """Record cost for budget tracking."""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_key = f"{project_id}:{today}"
        self.daily_costs[daily_key] = self.daily_costs.get(daily_key, 0) + cost

    async def request_approval(
        self,
        project_id: str,
        action_type: str,
        action_description: str,
        action_payload: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> ApprovalRequest:
        """Create an approval request."""
        request = ApprovalRequest(
            id=str(uuid4()),
            project_id=project_id,
            run_id=run_id,
            action_type=action_type,
            action_description=action_description,
            action_payload=action_payload,
            status="pending",
        )
        self.db.add(request)
        await self.db.flush()

        logger.info(
            "approval_requested",
            request_id=request.id,
            action_type=action_type,
            project_id=project_id,
        )

        return request

    async def approve_request(
        self,
        request_id: str,
        approved: bool,
        reason: str | None = None,
        decided_by: str = "user",
    ) -> ApprovalRequest | None:
        """Approve or deny a request."""
        result = await self.db.execute(
            select(ApprovalRequest).where(ApprovalRequest.id == request_id),
        )
        request = result.scalar_one_or_none()

        if not request:
            return None

        request.status = "approved" if approved else "denied"
        request.reviewer_notes = reason
        request.resolved_at = datetime.now(UTC).isoformat()

        await self.db.flush()

        logger.info(
            "approval_decision",
            request_id=request_id,
            approved=approved,
            decided_by=decided_by,
        )

        return request

    async def get_pending_approvals(
        self,
        project_id: str | None = None,
    ) -> list[ApprovalRequest]:
        """Get pending approval requests."""
        query = select(ApprovalRequest).where(
            ApprovalRequest.status == "pending",
        )

        if project_id:
            query = query.where(ApprovalRequest.project_id == project_id)

        query = query.order_by(ApprovalRequest.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def log_safety_event(
        self,
        event_type: str,
        details: dict[str, Any],
        project_id: str | None = None,
    ) -> AuditLog:
        """Log a safety-related event."""
        log = AuditLog(
            id=str(uuid4()),
            project_id=project_id,
            event_type=f"safety_{event_type}",
            actor="safety_system",
            action=event_type,
            details=details,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    def get_daily_stats(self, project_id: str) -> dict[str, Any]:
        """Get daily safety statistics."""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_key = f"{project_id}:{today}"

        return {
            "cost_today": self.daily_costs.get(daily_key, 0),
            "budget_remaining": max(0, self.policy.max_cost_per_day - self.daily_costs.get(daily_key, 0)),
            "max_daily_budget": self.policy.max_cost_per_day,
        }


# Safety policy instance
DEFAULT_SAFETY_POLICY = PermissionPolicy()
