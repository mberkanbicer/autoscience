"""Base academic source connector interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from typing import Any

import httpx

# ── Shared HTTP client defaults for all connectors ──────────────────────

# Multi-part timeout: connect, read, write, and pool timeouts
DEFAULT_TIMEOUT = httpx.Timeout(
    connect=10.0,    # time to establish a new TCP connection
    read=25.0,       # time to receive response body bytes
    write=20.0,      # time to send request body bytes
    pool=10.0,       # time to wait for a connection from the pool
)

# Connection-pool limits: max concurrent connections and keepalive
DEFAULT_LIMITS = httpx.Limits(
    max_connections=20,           # total connections allowed at once
    max_keepalive_connections=10,  # keepalive (idle) connections to reuse
    keepalive_expiry=30.0,        # seconds to keep idle connections alive
)


def create_connector_client(
    *,
    base_url: str = "",
    headers: dict[str, str] | None = None,
    timeout: httpx.Timeout | None = None,
    limits: httpx.Limits | None = None,
    **kwargs: Any,
) -> httpx.AsyncClient:
    """Create an :class:`httpx.AsyncClient` pre-configured with shared
    timeout and connection-pool defaults.

    Each connector should call this factory instead of constructing
    ``httpx.AsyncClient`` directly so that every source shares the
    same time-out and pooling behaviour.
    """
    params: dict[str, Any] = {
        "timeout": timeout or DEFAULT_TIMEOUT,
        "limits": limits or DEFAULT_LIMITS,
    }
    if base_url:
        params["base_url"] = base_url
    if headers:
        params["headers"] = headers
    params.update(kwargs)
    return httpx.AsyncClient(**params)


@dataclass
class RawPaper:
    """Raw paper data from an academic source."""

    source: str  # connector name
    source_id: str  # ID in the source system
    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    doi: str | None = None
    abstract: str | None = None
    venue: str | None = None
    url: str | None = None
    citation_count: int | None = None
    paper_type: str | None = None  # research, review, survey, dataset, benchmark
    references: list[str] = field(default_factory=list)  # DOIs or source IDs
    raw_metadata: dict[str, Any] = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SearchQuery:
    """A search query for academic sources."""

    text: str
    year_from: int | None = None
    year_to: int | None = None
    limit: int = 20
    paper_type: str | None = None  # research, review, survey
    sort_by: str = "relevance"  # relevance, citations, date


@dataclass
class SearchResult:
    """Result from an academic source search."""

    source: str
    query: SearchQuery
    papers: list[RawPaper] = field(default_factory=list)
    total_results: int = 0
    has_more: bool = False
    next_offset: int | None = None


class AcademicConnector(ABC):
    """Abstract base class for academic source connectors."""

    @property
    @abstractmethod
    def connector_name(self) -> str:
        """Return the connector name."""
        ...

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Return the base API URL."""
        ...

    @abstractmethod
    async def search(self, query: SearchQuery) -> SearchResult:
        """Search for papers."""
        ...

    @abstractmethod
    async def get_paper(self, identifier: str) -> RawPaper | None:
        """Get a paper by DOI, PMID, or source ID."""
        ...

    @abstractmethod
    async def get_citations(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers that cite this paper."""
        ...

    @abstractmethod
    async def get_references(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers referenced by this paper."""
        ...

    async def health_check(self) -> bool:
        """Check if the source is accessible."""
        try:
            # Default implementation: try a simple search
            query = SearchQuery(text="test", limit=1)
            await self.search(query)
            return True
        except httpx.RequestError:
            return False
