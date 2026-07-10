"""Collaboration API schemas."""

from datetime import datetime

from pydantic import Field

from .base import BaseSchema


class UserResponse(BaseSchema):
    id: str
    email: str
    display_name: str
    created_at: datetime


class MemberCreate(BaseSchema):
    project_id: str
    email: str = Field(..., min_length=3)
    display_name: str | None = None
    role: str = Field(default="editor", pattern="^(owner|editor|viewer)$")


class MemberResponse(BaseSchema):
    id: str
    project_id: str
    user_id: str
    role: str
    email: str
    display_name: str
    created_at: datetime


class CommentCreate(BaseSchema):
    project_id: str
    entity_type: str = Field(..., pattern="^(paper|hypothesis|manuscript|idea|wiki)$")
    entity_id: str
    body: str = Field(..., min_length=1)


class CommentResponse(BaseSchema):
    id: str
    project_id: str
    user_id: str
    author_name: str
    entity_type: str
    entity_id: str
    body: str
    status: str
    created_at: datetime


class ReviewProposalCreate(BaseSchema):
    project_id: str
    title: str = Field(..., min_length=1)
    description: str | None = None
    entity_type: str = Field(..., pattern="^(paper|hypothesis|manuscript|idea|run)$")
    entity_id: str | None = None
    assignee_id: str | None = None


class ReviewProposalUpdate(BaseSchema):
    status: str | None = Field(None, pattern="^(pending|in_review|approved|rejected)$")
    assignee_id: str | None = None


class ReviewProposalResponse(BaseSchema):
    id: str
    project_id: str
    created_by_id: str
    created_by_name: str
    assignee_id: str | None
    assignee_name: str | None
    title: str
    description: str | None
    entity_type: str
    entity_id: str | None
    status: str
    created_at: datetime


class PeerReviewSimulation(BaseSchema):
    summary: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    recommendation: str
    confidence: float = Field(ge=0.0, le=1.0)
    simulated: bool = True
    llm_used: bool = False


class ActivityItem(BaseSchema):
    id: str
    type: str
    actor: str
    summary: str
    created_at: datetime
    details: dict = Field(default_factory=dict)


class ReviewNotification(BaseSchema):
    id: str
    proposal_id: str
    project_id: str
    title: str
    status: str
    assignee_id: str
    created_at: datetime
    read: bool = False
