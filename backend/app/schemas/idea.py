"""Idea schemas."""

from pydantic import Field

from .base import BaseSchema, TimestampSchema


class IdeaCreate(BaseSchema):
    """Schema for creating an idea."""

    text: str = Field(..., min_length=1)
    flexibility: float | None = Field(None, ge=0.0, le=1.0)


class IdeaUpdate(BaseSchema):
    """Schema for updating an idea."""

    current_text: str | None = None
    flexibility: float | None = Field(None, ge=0.0, le=1.0)
    status: str | None = None


class IdeaScoreResponse(BaseSchema):
    """Schema for idea score response."""

    novelty: float | None = None
    feasibility: float | None = None
    importance: float | None = None
    evidence_support: float | None = None
    validation_clarity: float | None = None
    differentiation: float | None = None
    data_availability: float | None = None
    skill_leverage: float | None = None
    user_alignment: float | None = None
    prior_art_risk: float | None = None
    safety_risk: float | None = None
    cost_risk: float | None = None
    overall_value: float | None = None
    scoring_rationale: str | None = None


class IdeaResponse(TimestampSchema):
    """Schema for idea response."""

    project_id: str
    origin: str
    initial_text: str
    current_text: str
    flexibility: float | None = None
    status: str
    classification: str | None = None
    overall_score: float | None = None
    classification_reason: str | None = None


class IdeaVersionResponse(TimestampSchema):
    """Schema for idea version response."""

    idea_id: str
    version_number: int
    text: str
    change_reason: str | None = None


class IdeaDecisionResponse(TimestampSchema):
    """Schema for idea decision response."""

    idea_id: str
    run_id: str | None = None
    decision: str
    reason: str | None = None


class IdeaDetailResponse(IdeaResponse):
    """Schema for detailed idea response."""

    scores: list[IdeaScoreResponse] = Field(default_factory=list)
    versions: list[IdeaVersionResponse] = Field(default_factory=list)
    decisions: list[IdeaDecisionResponse] = Field(default_factory=list)
    linked_papers: list[str] = Field(default_factory=list)
    linked_conflicts: list[str] = Field(default_factory=list)
    linked_questions: list[str] = Field(default_factory=list)
    linked_hypotheses: list[str] = Field(default_factory=list)
