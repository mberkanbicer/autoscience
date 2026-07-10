"""Core research engines."""

from .clustering import ClusteringEngine, ClusteringResult, PaperCluster
from .conflict_detection import Conflict, ConflictDetectionEngine, ConflictDetectionResult, Gap
from .deduplication import (
    deduplicate_papers,
    group_papers_by_type,
    group_papers_by_venue,
    group_papers_by_year,
    normalize_doi,
    normalize_title,
    select_papers_for_analysis,
    titles_are_similar,
)
from .hypothesis_generation import (
    Hypothesis,
    HypothesisGenerationEngine,
    HypothesisGenerationResult,
)
from .idle_cognition import IdleCognitionEngine, IdleConfig, IdleCycleResult
from .keyword_engine import KeywordExpansion, KeywordExpansionEngine, SearchPlan, SearchQueryPlan
from .literature_engine import LiteratureEngine, LiteratureResult, RankedPaper
from .paper_analysis import Claim, PaperAnalysisEngine, PaperAnalysisResult
from .question_generation import (
    QuestionGenerationEngine,
    QuestionGenerationResult,
    ResearchQuestion,
)
from .scoring import IdeaScore, IdeaScoringEngine, ScoringResult
from .validation_planning import (
    DatasetCandidate,
    ValidationPlan,
    ValidationPlanningEngine,
    ValidationPlanResult,
)

__all__ = [
    # Keyword Engine
    "KeywordExpansionEngine",
    "KeywordExpansion",
    "SearchPlan",
    "SearchQueryPlan",
    # Literature Engine
    "LiteratureEngine",
    "LiteratureResult",
    "RankedPaper",
    # Paper Analysis
    "PaperAnalysisEngine",
    "PaperAnalysisResult",
    "Claim",
    # Clustering
    "ClusteringEngine",
    "ClusteringResult",
    "PaperCluster",
    # Conflict Detection
    "ConflictDetectionEngine",
    "ConflictDetectionResult",
    "Conflict",
    "Gap",
    # Question Generation
    "QuestionGenerationEngine",
    "QuestionGenerationResult",
    "ResearchQuestion",
    # Hypothesis Generation
    "HypothesisGenerationEngine",
    "HypothesisGenerationResult",
    "Hypothesis",
    # Validation Planning
    "ValidationPlanningEngine",
    "ValidationPlanResult",
    "ValidationPlan",
    "DatasetCandidate",
    # Scoring
    "IdeaScoringEngine",
    "IdeaScore",
    "ScoringResult",
    # Idle Cognition
    "IdleCognitionEngine",
    "IdleCycleResult",
    "IdleConfig",
    # Deduplication
    "deduplicate_papers",
    "select_papers_for_analysis",
    "group_papers_by_type",
    "group_papers_by_year",
    "group_papers_by_venue",
    "titles_are_similar",
    "normalize_title",
    "normalize_doi",
]
