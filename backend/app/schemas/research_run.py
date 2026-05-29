"""Research run schemas."""

from datetime import datetime

from pydantic import Field

from .base import BaseSchema, TimestampSchema


class ResearchRunCreate(BaseSchema):
    """Schema for creating a research run."""

    idea_id: str | None = None
    run_type: str = Field(..., pattern="^(user_directed|flexible_user|idle_autonomous|validation|skill_refinement)$")
    max_minutes: int = Field(default=60, ge=0)
    max_sources: int = Field(default=50, ge=0)
    max_cost_usd: float = Field(default=5.0, ge=0)


class ResearchRunUpdate(BaseSchema):
    """Schema for updating a research run."""

    state: str | None = Field(
        None,
        pattern="^(created|running|paused|waiting_for_approval|completed|failed|cancelled)$",
    )


class ResearchRunResponse(TimestampSchema):
    """Schema for research run response."""

    project_id: str
    idea_id: str | None = None
    run_type: str
    state: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    max_minutes: int
    max_sources: int
    max_cost_usd: float


class ResearchRunEventResponse(TimestampSchema):
    """Schema for research run event response."""

    run_id: str
    event_type: str
    actor: str | None = None
    details: dict | None = None


class ToolCallResponse(TimestampSchema):
    """Schema for tool call response."""

    run_id: str
    agent_role: str | None = None
    tool_name: str
    input_json: dict | None = None
    output_json: dict | None = None
    duration_ms: int | None = None
    success: bool
    error_message: str | None = None


class IdleCycleResponse(TimestampSchema):
    """Schema for idle cycle response."""

    project_id: str
    run_id: str | None = None
    idle_mode: str | None = None
    trigger_reason: str | None = None
    ideas_generated: int
    questions_generated: int
    hypotheses_generated: int
    skills_created: int
    duration_seconds: int | None = None
    cost_usd: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
