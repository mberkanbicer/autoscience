"""Audit and logging models."""

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class AuditLog(BaseModel):
    """Audit log entry for tracking system actions."""

    __tablename__ = "audit_logs"

    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(ForeignKey("research_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ApprovalRequest(BaseModel):
    """Approval request for actions requiring user consent."""

    __tablename__ = "approval_requests"

    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(ForeignKey("research_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", index=True
    )  # pending | approved | denied
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[str | None] = mapped_column(nullable=True)


class SystemEvent(BaseModel):
    """System-level events (startup, errors, etc.)."""

    __tablename__ = "system_events"

    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
