"""Pydantic schemas for API request/response validation."""

from .base import BaseSchema, TimestampSchema, PaginatedResponse, ErrorResponse
from .project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectStats
from .idea import (
    IdeaCreate,
    IdeaUpdate,
    IdeaResponse,
    IdeaDetailResponse,
    IdeaScoreResponse,
    IdeaVersionResponse,
    IdeaDecisionResponse,
)
from .research_run import (
    ResearchRunCreate,
    ResearchRunUpdate,
    ResearchRunResponse,
    ResearchRunEventResponse,
    ToolCallResponse,
    IdleCycleResponse,
)
from .paper import (
    PaperCreate,
    PaperUpdate,
    PaperResponse,
    PaperAnalysisResponse,
    PaperSearchRequest,
    PaperClusterResponse,
    ClusterConflictResponse,
)
from .skill import SkillCreate, SkillUpdate, SkillResponse, SkillVersionResponse, SkillUsageResponse
from .research_question import (
    ResearchQuestionCreate,
    ResearchQuestionResponse,
    HypothesisCreate,
    HypothesisUpdate,
    HypothesisResponse,
    ValidationPlanCreate,
    ValidationPlanResponse,
)
from .report import (
    ResearchReportResponse,
    KnowledgeNoteCreate,
    KnowledgeNoteResponse,
    AuditLogResponse,
    ApprovalRequestResponse,
    DatasetResponse,
    AnalysisRunResponse,
    AnalysisArtifactResponse,
)

__all__ = [
    # Base
    "BaseSchema",
    "TimestampSchema",
    "PaginatedResponse",
    "ErrorResponse",
    # Project
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectStats",
    # Idea
    "IdeaCreate",
    "IdeaUpdate",
    "IdeaResponse",
    "IdeaDetailResponse",
    "IdeaScoreResponse",
    "IdeaVersionResponse",
    "IdeaDecisionResponse",
    # Research Run
    "ResearchRunCreate",
    "ResearchRunUpdate",
    "ResearchRunResponse",
    "ResearchRunEventResponse",
    "ToolCallResponse",
    "IdleCycleResponse",
    # Paper
    "PaperCreate",
    "PaperUpdate",
    "PaperResponse",
    "PaperAnalysisResponse",
    "PaperSearchRequest",
    "PaperClusterResponse",
    "ClusterConflictResponse",
    # Skill
    "SkillCreate",
    "SkillUpdate",
    "SkillResponse",
    "SkillVersionResponse",
    "SkillUsageResponse",
    # Research Question
    "ResearchQuestionCreate",
    "ResearchQuestionResponse",
    "HypothesisCreate",
    "HypothesisUpdate",
    "HypothesisResponse",
    "ValidationPlanCreate",
    "ValidationPlanResponse",
    # Report
    "ResearchReportResponse",
    "KnowledgeNoteCreate",
    "KnowledgeNoteResponse",
    "AuditLogResponse",
    "ApprovalRequestResponse",
    "DatasetResponse",
    "AnalysisRunResponse",
    "AnalysisArtifactResponse",
]
