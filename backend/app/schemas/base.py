"""Base Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseSchema(PydanticBaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(BaseSchema):
    """Schema with timestamps."""

    id: str
    created_at: datetime
    updated_at: datetime | None = None


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper."""

    success: bool = True
    data: Any = None
    error: Any = None
    meta: dict | None = None


class ErrorResponse(BaseSchema):
    """Error response wrapper."""

    success: bool = False
    data: None = None
    error: dict
