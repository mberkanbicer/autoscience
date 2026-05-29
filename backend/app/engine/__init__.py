"""Core research engines."""

from .keyword_engine import KeywordExpansionEngine, KeywordExpansion, SearchPlan, SearchQueryPlan
from .literature_engine import LiteratureEngine, LiteratureResult, RankedPaper
from .paper_analysis import PaperAnalysisEngine, PaperAnalysisResult, Claim
from .clustering import ClusteringEngine, ClusteringResult, PaperCluster
from .conflict_detection import ConflictDetectionEngine, ConflictDetectionResult, Conflict, Gap
from .question_generation import QuestionGenerationEngine, QuestionGenerationResult, ResearchQuestion
from .hypothesis_generation import HypothesisGenerationEngine, HypothesisGenerationResult, Hypothesis
from .validation_planning import ValidationPlanningEngine, ValidationPlanResult, ValidationPlan, DatasetCandidate
from .scoring import IdeaScoringEngine, IdeaScore, ScoringResult
from .idle_cognition import IdleCognitionEngine, IdleCycleResult, IdleConfig
from .deduplication import (
    deduplicate_papers,
    select_papers_for_analysis,
    group_papers_by_type,
    group_papers_by_year,
    group_papers_by_venue,
    titles_are_similar,
    normalize_title,
    normalize_doi,
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
