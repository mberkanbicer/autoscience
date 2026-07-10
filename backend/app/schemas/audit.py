"""Audit schemas."""

from datetime import datetime

from .base import BaseSchema, TimestampSchema


class AuditLogResponse(TimestampSchema):
    """Schema for audit log response."""

    project_id: str | None = None
    run_id: str | None = None
    event_type: str
    actor: str | None = None
    action: str | None = None
    details: dict | None = None


class SystemEventResponse(TimestampSchema):
    """Schema for system event response."""

    event_type: str
    details: dict | None = None


class ApprovalRequestResponse(TimestampSchema):
    """Schema for approval request response."""

    project_id: str | None = None
    run_id: str | None = None
    action_type: str
    action_description: str | None = None
    action_payload: dict | None = None
    status: str
    reviewer_notes: str | None = None
    resolved_at: datetime | None = None


class ApprovalDecision(BaseSchema):
    """Schema for approval decision input."""

    approved: bool
    reviewer_notes: str | None = None


class ToolCallLogRequest(BaseSchema):
    """Schema for logging a tool call."""

    tool_name: str
    agent_role: str | None = None
    input_json: dict | None = None
    output_json: dict | None = None
    duration_ms: int | None = None
    success: bool = True
    error_message: str | None = None
