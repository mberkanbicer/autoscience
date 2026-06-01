"""Dataset schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DatasetCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    source_url: str | None = None
    format: str | None = Field(None, max_length=50)
    size_bytes: int | None = None
    row_count: int | None = None
    column_count: int | None = None
    schema_json: dict[str, Any] | None = None


class DatasetResponse(BaseModel):
    id: str
    project_id: str
    name: str | None
    description: str | None
    source_url: str | None
    format: str | None
    size_bytes: int | None
    row_count: int | None
    column_count: int | None
    schema_json: dict[str, Any] | None
    created_at: datetime | None
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class DatasetUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    source_url: str | None = None
    size_bytes: int | None = None
    row_count: int | None = None
    column_count: int | None = None
