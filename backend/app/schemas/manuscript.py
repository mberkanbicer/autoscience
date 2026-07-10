"""Manuscript schemas."""

from pydantic import Field

from .base import BaseSchema, TimestampSchema


class ManuscriptCreate(BaseSchema):
    """Schema for creating a manuscript."""

    project_id: str
    title: str = Field(..., min_length=1, max_length=500)
    run_id: str | None = None


class ManuscriptUpdate(BaseSchema):
    """Schema for updating a manuscript."""

    title: str | None = None
    content_latex: str | None = None
    status: str | None = None
    bibtex: str | None = None


class ManuscriptResponse(TimestampSchema):
    """Schema for manuscript response."""

    project_id: str
    run_id: str | None = None
    title: str
    content_latex: str | None = None
    version: int
    status: str
    compiled_url: str | None = None
    bibtex: str | None = None
