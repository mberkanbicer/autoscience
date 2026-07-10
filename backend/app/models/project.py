"""Project model."""

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from .organization import Organization


class Project(BaseModel):
    """A research project with domain, scope, and autonomy settings."""

    __tablename__ = "projects"

    # Multi-tenancy
    organization_id: Mapped[str | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True,
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Scope
    subject_scope: Mapped[list] = mapped_column(JSON, default=list)
    out_of_scope: Mapped[list] = mapped_column(JSON, default=list)

    # Autonomy settings
    default_flexibility: Mapped[float] = mapped_column(Float, default=0.6)

    # Idle research settings
    idle_research_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    idle_trigger_minutes: Mapped[int] = mapped_column(Integer, default=120)
    max_idle_cycles_per_day: Mapped[int] = mapped_column(Integer, default=3)
    max_sources_per_cycle: Mapped[int] = mapped_column(Integer, default=50)

    # Safety settings
    approval_required_for_external_actions: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    organization: Mapped[Organization | None] = relationship(back_populates="projects")
    ideas = relationship("Idea", back_populates="project", lazy="selectin", cascade="all, delete-orphan")
    research_runs = relationship("ResearchRun", back_populates="project", lazy="selectin", cascade="all, delete-orphan")
    papers = relationship("Paper", back_populates="project", lazy="selectin", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="project", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Project {self.name}>"
