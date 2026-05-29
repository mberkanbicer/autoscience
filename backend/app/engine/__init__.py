"""Core research engines."""

from .keyword_engine import KeywordExpansionEngine, KeywordExpansion, SearchPlan, SearchQueryPlan
from .literature_engine import LiteratureEngine, LiteratureResult, RankedPaper
from .paper_analysis import PaperAnalysisEngine, PaperAnalysisResult, Claim
from .clustering import ClusteringEngine, ClusteringResult, PaperCluster
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
