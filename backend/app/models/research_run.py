"""Research run models."""

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class ResearchRun(BaseModel):
    """A research run tracking the execution of a research workflow."""

    __tablename__ = "research_runs"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    idea_id: Mapped[str | None] = mapped_column(ForeignKey("ideas.id", ondelete="SET NULL"), nullable=True, index=True)
    run_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # user_directed | flexible_user | idle_autonomous | validation | skill_refinement
    state: Mapped[str] = mapped_column(
        String(50), default="created", index=True
    )  # created | running | paused | waiting_for_approval | completed | failed | cancelled

    # Timing
    started_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Budget
    max_minutes: Mapped[int] = mapped_column(Integer, default=60)
    max_sources: Mapped[int] = mapped_column(Integer, default=50)
    max_cost_usd: Mapped[float] = mapped_column(Float, default=5.0)

    # Relationships
    project = relationship("Project", back_populates="research_runs")
    events = relationship("ResearchRunEvent", back_populates="run", lazy="selectin")
    tool_calls = relationship("ToolCall", back_populates="run", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ResearchRun {self.id[:8]}... ({self.state})>"


class ResearchRunEvent(BaseModel):
    """Event in a research run timeline."""

    __tablename__ = "research_run_events"

    run_id: Mapped[str] = mapped_column(ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    run = relationship("ResearchRun", back_populates="events")


class ToolCall(BaseModel):
    """Record of a tool call during a research run."""

    __tablename__ = "tool_calls"

    run_id: Mapped[str] = mapped_column(ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    input_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    run = relationship("ResearchRun", back_populates="tool_calls")


class IdleCycle(BaseModel):
    """Record of an idle cognition cycle."""

    __tablename__ = "idle_cycles"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id: Mapped[str | None] = mapped_column(ForeignKey("research_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    idle_mode: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # frontier_scan | citation_conflict | revisit_rejected | cross_domain | skill_improvement | dataset_discovery
    trigger_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    ideas_generated: Mapped[int] = mapped_column(Integer, default=0)
    questions_generated: Mapped[int] = mapped_column(Integer, default=0)
    hypotheses_generated: Mapped[int] = mapped_column(Integer, default=0)
    skills_created: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
