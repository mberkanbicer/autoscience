"""Pydantic schemas for API request/response validation."""

from .audit import (
    ApprovalDecision,
    ApprovalRequestResponse,
    AuditLogResponse,
    SystemEventResponse,
    ToolCallLogRequest,
)
from .base import BaseSchema, ErrorResponse, PaginatedResponse, TimestampSchema
from .idea import (
    IdeaCreate,
    IdeaDecisionResponse,
    IdeaDetailResponse,
    IdeaResponse,
    IdeaScoreResponse,
    IdeaUpdate,
    IdeaVersionResponse,
)
from .paper import (
    ClusterConflictResponse,
    PaperAnalysisResponse,
    PaperClusterResponse,
    PaperCreate,
    PaperResponse,
    PaperSearchRequest,
    PaperUpdate,
)
from .project import ProjectCreate, ProjectResponse, ProjectStats, ProjectUpdate
from .report import (
    AnalysisArtifactResponse,
    AnalysisRunResponse,
    DatasetResponse,
    KnowledgeNoteCreate,
    KnowledgeNoteResponse,
    ResearchReportResponse,
)
from .research_question import (
    HypothesisCreate,
    HypothesisResponse,
    HypothesisUpdate,
    ResearchQuestionCreate,
    ResearchQuestionResponse,
    ValidationPlanCreate,
    ValidationPlanResponse,
)
from .research_run import (
    IdleCycleResponse,
    ResearchRunCreate,
    ResearchRunEventResponse,
    ResearchRunResponse,
    ResearchRunUpdate,
    ToolCallResponse,
)
from .research_state import (
    ClusterSummary,
    ConflictSummary,
    EventRecord,
    HypothesisSummary,
    PaperSummary,
    QuestionSummary,
    ResearchState,
    RunBudget,
    RunState,
    RunType,
    ScoreSummary,
    SkillSummary,
    ToolCallRecord,
)
from .skill import SkillCreate, SkillResponse, SkillUpdate, SkillUsageResponse, SkillVersionResponse

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
    "DatasetResponse",
    "AnalysisRunResponse",
    "AnalysisArtifactResponse",
    # Research State
    "ResearchState",
    "RunType",
    "RunState",
    "RunBudget",
    "PaperSummary",
    "ClusterSummary",
    "ConflictSummary",
    "QuestionSummary",
    "HypothesisSummary",
    "ScoreSummary",
    "SkillSummary",
    "ToolCallRecord",
    "EventRecord",
    # Audit
    "AuditLogResponse",
    "SystemEventResponse",
    "ApprovalRequestResponse",
    "ApprovalDecision",
    "ToolCallLogRequest",
]
