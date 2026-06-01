"""Research question and hypothesis models."""

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class ResearchQuestion(BaseModel):
    """A research question derived from conflicts and gaps."""

    __tablename__ = "research_questions"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    idea_id: Mapped[str | None] = mapped_column(ForeignKey("ideas.id", ondelete="SET NULL"), nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(ForeignKey("research_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    source_conflicts: Mapped[list] = mapped_column(JSON, default=list)
    source_gaps: Mapped[list] = mapped_column(JSON, default=list)
    rank: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="generated", index=True
    )  # generated | selected | hypothesis_created | rejected
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class Hypothesis(BaseModel):
    """A testable hypothesis derived from a research question."""

    __tablename__ = "hypotheses"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    idea_id: Mapped[str | None] = mapped_column(ForeignKey("ideas.id", ondelete="SET NULL"), nullable=True, index=True)
    question_id: Mapped[str | None] = mapped_column(ForeignKey("research_questions.id", ondelete="SET NULL"), nullable=True, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    independent_variable: Mapped[str | None] = mapped_column(Text, nullable=True)
    dependent_variable: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_direction: Mapped[str | None] = mapped_column(Text, nullable=True)
    baseline: Mapped[str | None] = mapped_column(Text, nullable=True)
    metric: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_requirement: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(
        String(50), default="draft", index=True
    )  # draft | validated | rejected | promoted


class ValidationPlan(BaseModel):
    """Validation plan for a hypothesis."""

    __tablename__ = "validation_plans"

    hypothesis_id: Mapped[str] = mapped_column(ForeignKey("hypotheses.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_candidates: Mapped[list] = mapped_column(JSON, default=list)
    benchmark_candidates: Mapped[list] = mapped_column(JSON, default=list)
    baselines: Mapped[list] = mapped_column(JSON, default=list)
    metrics: Mapped[list] = mapped_column(JSON, default=list)
    experimental_design: Mapped[str | None] = mapped_column(Text, nullable=True)
    statistical_tests: Mapped[list] = mapped_column(JSON, default=list)
    simulation_option: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_artifacts: Mapped[list] = mapped_column(JSON, default=list)
    difficulty_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    feasibility_score: Mapped[float | None] = mapped_column(Float, nullable=True)
