"""Dataset schemas."""

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
    schema_data: dict[str, Any] | None = None


class DatasetUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    source_url: str | None = None
    size_bytes: int | None = None
    row_count: int | None = None
    column_count: int | None = None
