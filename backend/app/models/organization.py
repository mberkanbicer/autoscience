"""Multi-tenancy scaffolding — organization-level project isolation.

Organizations own projects and users. Users belong to organizations with roles.
This enables org-scoped access control, audit isolation, and resource quotas.
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Organization(BaseModel):
    """A tenant organization that owns projects and manages users."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="Verified email domain for auto-join")
    max_projects: Mapped[int] = mapped_column(Integer, default=10)
    max_users: Mapped[int] = mapped_column(Integer, default=25)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="Org-level feature flags and config")

    # Relationships
    members: Mapped[list[OrganizationMember]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    projects: Mapped[list[Project]] = relationship(back_populates="organization")

    def __repr__(self) -> str:
        return f"<Organization {self.slug}>"


class OrganizationMember(BaseModel):
    """A user's membership in an organization with role-based access."""

    __tablename__ = "organization_members"

    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="member",
    )  # owner | admin | member | viewer
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
    )

    # Relationships
    organization: Mapped[Organization] = relationship(back_populates="members")

    def __repr__(self) -> str:
        return f"<OrganizationMember org={self.organization_id} user={self.user_id} role={self.role}>"
