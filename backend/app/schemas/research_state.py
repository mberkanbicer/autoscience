"""Research state schema - the state object passed through workflows."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from .base import BaseSchema


class RunType(str, Enum):
    """Types of research runs."""

    USER_DIRECTED = "user_directed"
    FLEXIBLE_USER = "flexible_user"
    IDLE_AUTONOMOUS = "idle_autonomous"
    VALIDATION = "validation"
    SKILL_REFINEMENT = "skill_refinement"


class RunState(str, Enum):
    """States of a research run."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunBudget(BaseSchema):
    """Budget constraints for a research run."""

    max_minutes: int = 60
    max_sources: int = 50
    max_cost_usd: float = 5.0


class PaperSummary(BaseSchema):
    """Summary of a paper for state tracking."""

    id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    doi: str | None = None
    citation_count: int | None = None
    paper_type: str | None = None
    relevance_score: float | None = None


class ClusterSummary(BaseSchema):
    """Summary of a cluster for state tracking."""

    id: str
    name: str | None = None
    description: str | None = None
    cluster_type: str | None = None
    paper_count: int = 0
    representative_paper_id: str | None = None


class ConflictSummary(BaseSchema):
    """Summary of a conflict for state tracking."""

    id: str
    conflict_type: str
    description: str
    severity: float | None = None
    supporting_papers_count: int = 0
    opposing_papers_count: int = 0


class QuestionSummary(BaseSchema):
    """Summary of a research question for state tracking."""

    id: str
    question: str
    rank: float | None = None
    status: str
    source_conflicts_count: int = 0


class HypothesisSummary(BaseSchema):
    """Summary of a hypothesis for state tracking."""

    id: str
    statement: str
    confidence: float | None = None
    status: str
    has_validation_plan: bool = False


class ScoreSummary(BaseSchema):
    """Summary of an idea score for state tracking."""

    id: str
    overall_value: float | None = None
    classification: str | None = None
    scored_at: datetime | None = None


class SkillSummary(BaseSchema):
    """Summary of a skill for state tracking."""

    id: str
    name: str
    skill_type: str
    status: str
    version: str


class ToolCallRecord(BaseSchema):
    """Record of a tool call in the state."""

    id: str
    tool_name: str
    agent_role: str | None = None
    duration_ms: int | None = None
    success: bool = True
    timestamp: datetime | None = None


class EventRecord(BaseSchema):
    """Record of an event in the state."""

    id: str
    event_type: str
    actor: str | None = None
    timestamp: datetime | None = None


class ResearchState(BaseSchema):
    """The complete state object for a research workflow.

    This is passed between agents and workflows, tracking all
    context and progress of a research run.
    """

    # Run identification
    run_id: str
    project_id: str
    idea_id: str | None = None

    # Run configuration
    run_type: RunType
    current_phase: str = "initialized"
    state: RunState = RunState.CREATED

    # Idea context
    original_idea: str = ""
    current_idea: str = ""
    flexibility: float = 0.6

    # Budget tracking
    budget: RunBudget = Field(default_factory=RunBudget)
    minutes_elapsed: float = 0.0
    sources_searched: int = 0
    cost_usd: float = 0.0

    # Literature intelligence
    papers: list[PaperSummary] = Field(default_factory=list)
    clusters: list[ClusterSummary] = Field(default_factory=list)
    conflicts: list[ConflictSummary] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)  # Expanded keywords from plan_search

    # Research questions and hypotheses
    questions: list[QuestionSummary] = Field(default_factory=list)
    hypotheses: list[HypothesisSummary] = Field(default_factory=list)

    # Scoring and decisions
    scores: list[ScoreSummary] = Field(default_factory=list)
    current_classification: str | None = None

    # Skills
    skills_used: list[str] = Field(default_factory=list)  # skill IDs
    skills_created: list[str] = Field(default_factory=list)  # skill IDs

    # Execution tracking
    events: list[EventRecord] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)

    # Error tracking
    errors: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # Metadata
    started_at: datetime | None = None
    last_updated: datetime | None = None
    completed_at: datetime | None = None

    def add_event(self, event_type: str, actor: str | None = None, **kwargs: Any) -> None:
        """Add an event to the state."""
        from uuid import uuid4

        event = EventRecord(
            id=str(uuid4()),
            event_type=event_type,
            actor=actor,
            timestamp=datetime.utcnow(),
        )
        self.events.append(event)
        self.last_updated = datetime.utcnow()

    def add_tool_call(
        self,
        tool_name: str,
        agent_role: str | None = None,
        duration_ms: int | None = None,
        success: bool = True,
    ) -> None:
        """Add a tool call record to the state."""
        from uuid import uuid4

        tool_call = ToolCallRecord(
            id=str(uuid4()),
            tool_name=tool_name,
            agent_role=agent_role,
            duration_ms=duration_ms,
            success=success,
            timestamp=datetime.utcnow(),
        )
        self.tool_calls.append(tool_call)
        self.last_updated = datetime.utcnow()

    def add_error(self, error_type: str, message: str, details: dict[str, Any] | None = None) -> None:
        """Add an error to the state."""
        from uuid import uuid4

        error = {
            "id": str(uuid4()),
            "error_type": error_type,
            "message": message,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.errors.append(error)
        self.warnings.append(f"Error: {error_type} - {message}")
        self.last_updated = datetime.utcnow()

    def update_phase(self, phase: str) -> None:
        """Update the current phase."""
        self.current_phase = phase
        self.add_event("phase_changed", details={"new_phase": phase})

    def is_budget_exceeded(self) -> bool:
        """Check if any budget limit is exceeded."""
        return (
            self.minutes_elapsed >= self.budget.max_minutes
            or self.sources_searched >= self.budget.max_sources
            or self.cost_usd >= self.budget.max_cost_usd
        )

    def budget_remaining(self) -> dict[str, float]:
        """Get remaining budget as percentages."""
        return {
            "minutes": max(0, 1 - (self.minutes_elapsed / self.budget.max_minutes)),
            "sources": max(0, 1 - (self.sources_searched / self.budget.max_sources)),
            "cost": max(0, 1 - (self.cost_usd / self.budget.max_cost_usd)),
        }

    def to_snapshot(self) -> dict[str, Any]:
        """Export state as a JSON-serializable dictionary."""
        return self.model_dump(mode="json")
