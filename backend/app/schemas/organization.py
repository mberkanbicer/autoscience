"""Organization schemas for multi-tenancy."""

from pydantic import Field

from .base import BaseSchema, TimestampSchema


class OrganizationCreate(BaseSchema):
    """Schema for creating an organization."""

    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=100, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    domain: str | None = Field(None, max_length=255)
    max_projects: int = Field(default=10, ge=1, le=1000)
    max_users: int = Field(default=25, ge=1, le=10000)


class OrganizationUpdate(BaseSchema):
    """Schema for updating an organization."""

    name: str | None = Field(None, max_length=255)
    description: str | None = None
    domain: str | None = Field(None, max_length=255)
    max_projects: int | None = Field(None, ge=1, le=1000)
    max_users: int | None = Field(None, ge=1, le=10000)
    is_active: bool | None = None


class OrganizationResponse(TimestampSchema):
    """Schema for organization response."""

    name: str
    slug: str
    description: str | None = None
    domain: str | None = None
    max_projects: int = 10
    max_users: int = 25
    is_active: bool = True


class OrganizationMemberResponse(TimestampSchema):
    """Schema for organization member response."""

    organization_id: str
    user_id: str
    role: str = "member"
    is_active: bool = True
