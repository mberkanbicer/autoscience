"""Academic source connectors.

Re-exports base types, all implemented connector classes (except SearXNG and
Firecrawl which have circular-import-sensitive CacheService dependencies),
and serialization helpers.

ConnectorManager and create_default_manager are importable directly from
  app.connectors.manager
to avoid the circular import triggered by loading manager.py (which imports
CacheService) during package init.
"""

from .arxiv import ArxivConnector
from .base import AcademicConnector, RawPaper, SearchQuery, SearchResult
from .core import COREConnector
from .crossref import CrossrefConnector
from .doaj import DOAJConnector
from .openalex import OpenAlexConnector
from .pubmed import PubMedConnector
from .semantic_scholar import SemanticScholarConnector
from .serialization import (
    paper_from_dict,
    paper_to_dict,
    search_result_from_dict,
    search_result_to_dict,
)
from .unpaywall import UnpaywallConnector

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
    "DOAJConnector",
    "COREConnector",
    "UnpaywallConnector",
    "paper_from_dict",
    "paper_to_dict",
    "search_result_from_dict",
    "search_result_to_dict",
]
