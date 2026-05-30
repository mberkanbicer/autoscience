"""Idea models."""

from sqlalchemy import Float, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Idea(BaseModel):
    """A research idea with version history and scoring."""

    __tablename__ = "ideas"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    origin: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # user_prompt | idle_generated | literature_gap | skill_generated | revived
    initial_text: Mapped[str] = mapped_column(Text, nullable=False)
    current_text: Mapped[str] = mapped_column(Text, nullable=False)
    flexibility: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="active", index=True
    )  # active | archived | rejected | promoted | under_validation
    classification: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )  # high_value | promising | incremental | weak | reject
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    classification_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="ideas")
    versions = relationship("IdeaVersion", back_populates="idea", lazy="selectin")
    scores = relationship("IdeaScore", back_populates="idea", lazy="selectin")
    classifications = relationship("IdeaClassification", back_populates="idea", lazy="selectin")
    decisions = relationship("IdeaDecision", back_populates="idea", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Idea {self.id[:8]}... ({self.status})>"


class IdeaVersion(BaseModel):
    """Version history for an idea."""

    __tablename__ = "idea_versions"

    idea_id: Mapped[str] = mapped_column(ForeignKey("ideas.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    idea = relationship("Idea", back_populates="versions")


class IdeaScore(BaseModel):
    """Score history for an idea."""

    __tablename__ = "idea_scores"

    idea_id: Mapped[str] = mapped_column(ForeignKey("ideas.id"), nullable=False, index=True)
    novelty: Mapped[float | None] = mapped_column(Float, nullable=True)
    feasibility: Mapped[float | None] = mapped_column(Float, nullable=True)
    importance: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_support: Mapped[float | None] = mapped_column(Float, nullable=True)
    validation_clarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    differentiation: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_availability: Mapped[float | None] = mapped_column(Float, nullable=True)
    skill_leverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    user_alignment: Mapped[float | None] = mapped_column(Float, nullable=True)
    prior_art_risk: Mapped[float | None] = mapped_column(Float, nullable=True)
    safety_risk: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_risk: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    scoring_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    idea = relationship("Idea", back_populates="scores")


class IdeaClassification(BaseModel):
    """Classification history for an idea."""

    __tablename__ = "idea_classifications"

    idea_id: Mapped[str] = mapped_column(ForeignKey("ideas.id"), nullable=False, index=True)
    classification: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    idea = relationship("Idea", back_populates="classifications")


class IdeaDecision(BaseModel):
    """Decision history for an idea."""

    __tablename__ = "idea_decisions"

    idea_id: Mapped[str] = mapped_column(ForeignKey("ideas.id"), nullable=False, index=True)
    run_id: Mapped[str | None] = mapped_column(ForeignKey("research_runs.id"), nullable=True, index=True)
    decision: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # continue | revise | pivot | archive | reject | promote
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    idea = relationship("Idea", back_populates="decisions")
