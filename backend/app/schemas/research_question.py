"""Research question and hypothesis schemas."""

from pydantic import Field

from .base import BaseSchema, TimestampSchema


class ResearchQuestionCreate(BaseSchema):
    """Schema for creating a research question."""

    question: str = Field(..., min_length=1)
    source_conflicts: list[str] = Field(default_factory=list)
    source_gaps: list[str] = Field(default_factory=list)
    idea_id: str | None = None


class ResearchQuestionResponse(TimestampSchema):
    """Schema for research question response."""

    project_id: str
    idea_id: str | None = None
    run_id: str | None = None
    question: str
    source_conflicts: list[str] = Field(default_factory=list)
    source_gaps: list[str] = Field(default_factory=list)
    rank: float | None = None
    status: str
    rejection_reason: str | None = None


class HypothesisCreate(BaseSchema):
    """Schema for creating a hypothesis."""

    question_id: str | None = None
    statement: str = Field(..., min_length=1)
    independent_variable: str | None = None
    dependent_variable: str | None = None
    context: str | None = None
    expected_direction: str | None = None
    baseline: str | None = None
    metric: str | None = None
    dataset_requirement: str | None = None
    failure_condition: str | None = None
    idea_id: str | None = None


class HypothesisUpdate(BaseSchema):
    """Schema for updating a hypothesis."""

    statement: str | None = None
    independent_variable: str | None = None
    dependent_variable: str | None = None
    context: str | None = None
    expected_direction: str | None = None
    baseline: str | None = None
    metric: str | None = None
    dataset_requirement: str | None = None
    failure_condition: str | None = None
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    status: str | None = Field(
        None, pattern="^(draft|validated|rejected|promoted)$"
    )


class HypothesisResponse(TimestampSchema):
    """Schema for hypothesis response."""

    project_id: str
    idea_id: str | None = None
    question_id: str | None = None
    statement: str
    independent_variable: str | None = None
    dependent_variable: str | None = None
    context: str | None = None
    expected_direction: str | None = None
    baseline: str | None = None
    metric: str | None = None
    dataset_requirement: str | None = None
    failure_condition: str | None = None
    confidence: float | None = None
    version: int
    status: str


class ValidationPlanCreate(BaseSchema):
    """Schema for creating a validation plan."""

    hypothesis_id: str
    dataset_candidates: list[dict] = Field(default_factory=list)
    benchmark_candidates: list[str] = Field(default_factory=list)
    baselines: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    experimental_design: str | None = None
    statistical_tests: list[str] = Field(default_factory=list)
    simulation_option: str | None = None
    expected_artifacts: list[str] = Field(default_factory=list)
    difficulty_estimate: float | None = Field(None, ge=0.0, le=10.0)
    cost_estimate: float | None = Field(None, ge=0.0)
    feasibility_score: float | None = Field(None, ge=0.0, le=10.0)


class ValidationPlanResponse(TimestampSchema):
    """Schema for validation plan response."""

    hypothesis_id: str
    dataset_candidates: list[dict] = Field(default_factory=list)
    benchmark_candidates: list[str] = Field(default_factory=list)
    baselines: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    experimental_design: str | None = None
    statistical_tests: list[str] = Field(default_factory=list)
    simulation_option: str | None = None
    expected_artifacts: list[str] = Field(default_factory=list)
    difficulty_estimate: float | None = None
    cost_estimate: float | None = None
    feasibility_score: float | None = None
