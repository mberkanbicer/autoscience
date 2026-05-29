"""Report and knowledge note schemas."""

from pydantic import Field

from .base import BaseSchema, TimestampSchema


class ResearchReportResponse(TimestampSchema):
    """Schema for research report response."""

    project_id: str
    run_id: str | None = None
    idea_id: str | None = None
    title: str | None = None
    content_markdown: str | None = None
    content_html: str | None = None
    report_type: str | None = None


class KnowledgeNoteCreate(BaseSchema):
    """Schema for creating a knowledge note."""

    note_type: str = Field(
        ...,
        pattern="^(paper|cluster|conflict|hypothesis|skill|project)$",
    )
    entity_id: str | None = None
    title: str | None = Field(None, max_length=255)
    content: str | None = None
    linked_notes: list[str] = Field(default_factory=list)


class KnowledgeNoteResponse(TimestampSchema):
    """Schema for knowledge note response."""

    project_id: str
    note_type: str
    entity_id: str | None = None
    title: str | None = None
    content: str | None = None
    linked_notes: list[str] = Field(default_factory=list)


class AuditLogResponse(TimestampSchema):
    """Schema for audit log response."""

    project_id: str | None = None
    run_id: str | None = None
    event_type: str
    actor: str | None = None
    action: str | None = None
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
    resolved_at: str | None = None


class DatasetResponse(TimestampSchema):
    """Schema for dataset response."""

    project_id: str
    name: str | None = None
    description: str | None = None
    source_url: str | None = None
    format: str | None = None
    size_bytes: int | None = None
    row_count: int | None = None
    column_count: int | None = None
    schema_json: dict | None = None


class AnalysisRunResponse(TimestampSchema):
    """Schema for analysis run response."""

    hypothesis_id: str | None = None
    dataset_id: str | None = None
    script: str | None = None
    status: str | None = None
    error_message: str | None = None


class AnalysisArtifactResponse(TimestampSchema):
    """Schema for analysis artifact response."""

    analysis_run_id: str
    artifact_type: str | None = None
    file_path: str | None = None
    description: str | None = None
