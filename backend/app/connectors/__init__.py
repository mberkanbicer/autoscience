"""Academic source connectors."""

from .base import AcademicConnector, RawPaper, SearchQuery, SearchResult
from .openalex import OpenAlexConnector
from .semantic_scholar import SemanticScholarConnector
from .crossref import CrossrefConnector
from .arxiv import ArxivConnector
from .pubmed import PubMedConnector
from .manager import ConnectorManager, create_default_manager

__all__ = [
    "AcademicConnector",
    "RawPaper",
    "SearchQuery",
    "SearchResult",
    "OpenAlexConnector",
    "SemanticScholarConnector",
    "CrossrefConnector",
    "ArxivConnector",
    "PubMedConnector",
    "ConnectorManager",
    "create_default_manager",
]
