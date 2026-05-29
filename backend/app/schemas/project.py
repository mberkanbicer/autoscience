"""Project schemas."""

from pydantic import Field

from .base import BaseSchema, TimestampSchema


class ProjectCreate(BaseSchema):
    """Schema for creating a project."""

    name: str = Field(..., max_length=255)
    domain: str = Field(..., max_length=500)
    description: str | None = None
    subject_scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    default_flexibility: float = Field(default=0.6, ge=0.0, le=1.0)
    idle_research_enabled: bool = True
    idle_trigger_minutes: int = Field(default=120, ge=0)
    max_idle_cycles_per_day: int = Field(default=3, ge=0)
    max_sources_per_cycle: int = Field(default=50, ge=0)
    approval_required_for_external_actions: bool = True


class ProjectUpdate(BaseSchema):
    """Schema for updating a project."""

    name: str | None = Field(None, max_length=255)
    domain: str | None = Field(None, max_length=500)
    description: str | None = None
    subject_scope: list[str] | None = None
    out_of_scope: list[str] | None = None
    default_flexibility: float | None = Field(None, ge=0.0, le=1.0)
    idle_research_enabled: bool | None = None
    idle_trigger_minutes: int | None = Field(None, ge=0)
    max_idle_cycles_per_day: int | None = Field(None, ge=0)
    max_sources_per_cycle: int | None = Field(None, ge=0)
    approval_required_for_external_actions: bool | None = None


class ProjectResponse(TimestampSchema):
    """Schema for project response."""

    name: str
    domain: str
    description: str | None = None
    subject_scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    default_flexibility: float
    idle_research_enabled: bool
    idle_trigger_minutes: int
    max_idle_cycles_per_day: int
    max_sources_per_cycle: int
    approval_required_for_external_actions: bool


class ProjectStats(BaseSchema):
    """Schema for project statistics."""

    total_ideas: int = 0
    active_ideas: int = 0
    rejected_ideas: int = 0
    total_runs: int = 0
    active_runs: int = 0
    total_papers: int = 0
    total_skills: int = 0
    total_conflicts: int = 0
    total_questions: int = 0
    total_hypotheses: int = 0
