"""Dataset schemas."""

from typing import Any

from pydantic import Field

from .base import BaseSchema, TimestampSchema


class DatasetCreate(BaseSchema):
    project_id: str
    name: str = Field(..., max_length=255)
    description: str | None = None
    source_url: str | None = None
    format: str | None = Field(None, max_length=50)
    size_bytes: int | None = None
    row_count: int | None = None
    column_count: int | None = None
    column_schema: dict[str, Any] | None = None
    # Provenance
    uploaded_by: str | None = None
    original_filename: str | None = None
    provenance: str | None = Field(None, max_length=50)


class DatasetUpdate(BaseSchema):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    source_url: str | None = None
    size_bytes: int | None = None
    row_count: int | None = None
    column_count: int | None = None


class DatasetResponse(TimestampSchema):
    project_id: str
    name: str | None = None
    description: str | None = None
    source_url: str | None = None
    format: str | None = None
    size_bytes: int | None = None
    row_count: int | None = None
    column_count: int | None = None
    uploaded_by: str | None = None
    original_filename: str | None = None
    provenance: str | None = None


class DatasetUploadResponse(BaseSchema):
    id: str
    name: str
    format: str
    row_count: int
    column_count: int
    size_bytes: int
    column_schema: dict[str, Any]
    preview_rows: list[dict[str, Any]]
    warnings: list[str]
