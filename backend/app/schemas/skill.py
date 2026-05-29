"""Skill schemas."""

from pydantic import Field

from .base import BaseSchema, TimestampSchema


class SkillCreate(BaseSchema):
    """Schema for creating a skill."""

    name: str = Field(..., max_length=255)
    skill_type: str = Field(
        ...,
        pattern="^(planning|functional|atomic|domain|evaluation|data|reporting|safety)$",
    )
    purpose: str | None = None
    trigger_conditions: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    procedure: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    project_id: str | None = None


class SkillUpdate(BaseSchema):
    """Schema for updating a skill."""

    name: str | None = Field(None, max_length=255)
    purpose: str | None = None
    trigger_conditions: list[str] | None = None
    inputs: list[str] | None = None
    procedure: list[str] | None = None
    outputs: list[str] | None = None
    status: str | None = Field(
        None,
        pattern="^(candidate|tested|active|revised|deprecated|retired)$",
    )


class SkillResponse(TimestampSchema):
    """Schema for skill response."""

    project_id: str | None = None
    name: str
    skill_type: str
    purpose: str | None = None
    trigger_conditions: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    procedure: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    status: str
    version: str
    times_used: int
    successful_uses: int
    average_score_improvement: float | None = None
    failure_cases: list[str] = Field(default_factory=list)
    domains_where_it_works: list[str] = Field(default_factory=list)
    domains_where_it_fails: list[str] = Field(default_factory=list)


class SkillVersionResponse(TimestampSchema):
    """Schema for skill version response."""

    skill_id: str
    version: str
    changes: str | None = None
    procedure: list[str] | None = None


class SkillUsageResponse(TimestampSchema):
    """Schema for skill usage response."""

    skill_id: str
    run_id: str | None = None
    success: bool
    score_before: float | None = None
    score_after: float | None = None
    notes: str | None = None
