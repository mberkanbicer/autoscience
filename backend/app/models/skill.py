"""Skill models."""

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Skill(BaseModel):
    """A reusable research skill."""

    __tablename__ = "skills"

    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    skill_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # planning | functional | atomic | domain | evaluation | data | reporting | safety
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_conditions: Mapped[list] = mapped_column(JSON, default=list)
    inputs: Mapped[list] = mapped_column(JSON, default=list)
    procedure: Mapped[list] = mapped_column(JSON, default=list)
    outputs: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(
        String(50), default="candidate", index=True
    )  # candidate | tested | active | revised | deprecated | retired
    version: Mapped[str] = mapped_column(String(20), default="1.0")

    # Performance tracking
    times_used: Mapped[int] = mapped_column(Integer, default=0)
    successful_uses: Mapped[int] = mapped_column(Integer, default=0)
    average_score_improvement: Mapped[float | None] = mapped_column(Float, nullable=True)
    failure_cases: Mapped[list] = mapped_column(JSON, default=list)
    domains_where_it_works: Mapped[list] = mapped_column(JSON, default=list)
    domains_where_it_fails: Mapped[list] = mapped_column(JSON, default=list)

    # Relationships
    project = relationship("Project", back_populates="skills")
    versions = relationship("SkillVersion", back_populates="skill", lazy="selectin")
    usages = relationship("SkillUsage", back_populates="skill", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Skill {self.name} ({self.status})>"


class SkillVersion(BaseModel):
    """Version history for a skill."""

    __tablename__ = "skill_versions"

    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    changes: Mapped[str | None] = mapped_column(Text, nullable=True)
    procedure: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Relationships
    skill = relationship("Skill", back_populates="versions")


class SkillUsage(BaseModel):
    """Record of a skill being used in a research run."""

    __tablename__ = "skill_usages"

    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id: Mapped[str | None] = mapped_column(ForeignKey("research_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    score_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    skill = relationship("Skill", back_populates="usages")


class SkillEvaluation(BaseModel):
    """Evaluation of a skill's effectiveness."""

    __tablename__ = "skill_evaluations"

    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    evaluator: Mapped[str] = mapped_column(String(100), nullable=False)  # system | user
    rating: Mapped[float] = mapped_column(Float, nullable=False)  # 0-10
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
