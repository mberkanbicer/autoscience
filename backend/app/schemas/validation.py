"""Validation schemas for API requests."""

from pydantic import BaseModel, Field


class StartResearchRunRequest(BaseModel):
    """Schema for starting a research run."""

    project_id: str = Field(..., min_length=36, max_length=36)
    idea: str = Field(..., min_length=10, max_length=5000)
    run_type: str = Field(..., pattern=r"^(user_directed|flexible_user|idle_autonomous|validation|skill_refinement)$")
    flexibility: float = Field(default=0.6, ge=0, le=1.0)


class StartIdleCycleRequest(BaseModel):
    """Schema for starting an idle cognition cycle."""

    project_id: str = Field(..., min_length=36, pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
