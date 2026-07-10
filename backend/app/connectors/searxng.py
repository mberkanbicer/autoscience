"""SearXNG academic connector with caching support."""

from typing import Any

import httpx
import structlog

from app.services.cache_service import CacheService

from .base import AcademicConnector, RawPaper, SearchQuery, SearchResult, create_connector_client

logger = structlog.get_logger()


class SearXNGConnector(AcademicConnector):
    """Connector for SearXNG meta-search engine.

    Queries a self-hosted SearXNG instance for academic and general web results.
    Supports categories: science, general
    Supports engines: google scholar, semantic scholar, arxiv, etc.
    Results are cached via CacheService with configurable TTL.
    """

    def __init__(
        self,
        base_url: str = "https://search.bicers.me",
        cache_service: CacheService | None = None,
        cache_ttl: int = 3600,
        default_categories: list[str] | None = None,
        default_engines: list[str] | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.cache = cache_service
        self.cache_ttl = cache_ttl
        self.default_categories = default_categories or ["science", "general"]
        self.default_engines = default_engines or []

    @property
    def connector_name(self) -> str:
        return "searxng"

    @property
    def base_url(self) -> str:
        return self._base_url

    @base_url.setter
    def base_url(self, value: str):
        self._base_url = value

    async def search(
        self,
        query: SearchQuery,
        force_refresh: bool = False,
        categories: list[str] | None = None,
        engines: list[str] | None = None,
    ) -> SearchResult:
        """Search SearXNG with optional caching.

        Args:
            query: The search query.
            force_refresh: If True, bypass cache.
            categories: SearXNG categories (e.g., ["science", "general"]).
            engines: SearXNG engines (e.g., ["google scholar", "semantic scholar"]).

        """
        cats = categories or self.default_categories
        engs = engines or self.default_engines

        # Check cache first
        cache_kwargs = {
            "text": query.text,
            "year_from": query.year_from,
            "year_to": query.year_to,
            "limit": query.limit,
            "categories": cats,
            "engines": engs,
        }

        if self.cache:
            cached, hit = await self.cache.get(
                "searxng", force_refresh=force_refresh, **cache_kwargs,
            )
            if hit and cached:
                return self._deserialize_result(cached, query)

        # Build request parameters
        params = {
            "q": query.text,
            "format": "json",
        }
        if cats:
            params["categories"] = ",".join(cats)
        if engs:
            params["engines"] = ",".join(engs)
        if query.year_from:
            params["time_range"] = "year"  # SearXNG uses time_range, not year_from

        # Make request
        papers = []
        total = 0
        try:
            async with create_connector_client(timeout=httpx.Timeout(30.0)) as client:
                url = f"{self.base_url}/search"
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            total = data.get("number_of_results", 0)
            raw_results = data.get("results", [])

            # Convert to RawPaper
            for r in raw_results[: query.limit]:
                paper = self._result_to_paper(r, query)
                if paper:
                    papers.append(paper)

            logger.info(
                "searxng_search_completed",
                query=query.text,
                results=len(papers),
                total=total,
            )

        except httpx.HTTPStatusError as e:
            logger.error("searxng_http_error", status=e.response.status_code, query=query.text)
        except Exception as e:
            logger.error("searxng_search_failed", error=str(e), query=query.text, exc_info=True)

        result = SearchResult(
            source="searxng",
            query=query,
            papers=papers,
            total_results=total,
            has_more=total > query.limit,
        )

        # Cache the result
        if self.cache and papers:
            try:
                serialized = self._serialize_result(result)
                await self.cache.set(
                    "searxng", serialized, ttl_seconds=self.cache_ttl, **cache_kwargs,
                )
            except Exception as e:
                logger.warning("searxng_cache_set_failed", error=str(e), exc_info=True)

        return result

    async def get_paper(self, identifier: str) -> RawPaper | None:
        """Get a paper by URL or DOI (search-based lookup)."""
        query = SearchQuery(text=identifier, limit=5)
        result = await self.search(query)
        for paper in result.papers:
            if paper.doi and identifier.lower() in (paper.doi or "").lower():
                return paper
            if paper.url and identifier in (paper.url or ""):
                return paper
        return result.papers[0] if result.papers else None

    async def get_citations(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get citing papers (SearXNG doesn't support this directly)."""
        return []

    async def get_references(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get referenced papers (SearXNG doesn't support this directly)."""
        return []

    def _result_to_paper(self, r: dict[str, Any], query: SearchQuery) -> RawPaper | None:
        """Convert a SearXNG result to a RawPaper."""
        title = r.get("title", "").strip()
        if not title:
            return None

        # Extract year from publishedDate or pubdate
        year = None
        pub_date = r.get("publishedDate") or r.get("pubdate")
        if pub_date and isinstance(pub_date, str):
            try:
                year = int(pub_date[:4])
            except (ValueError, IndexError):
                pass

        # Extract DOI from URL if present
        doi = None
        url = r.get("url", "")
        if "doi.org/" in url:
            doi = url.split("doi.org/", 1)[-1]
        elif "/doi/" in url:
            doi = url.split("/doi/", 1)[-1]

        # Determine paper type from category
        paper_type = None
        category = r.get("category", "")
        if category in ("science", "scientific"):
            paper_type = "research"

        # Build authors from content (SearXNG doesn't always provide authors)
        authors = []
        content = r.get("content", "")

        return RawPaper(
            source="searxng",
            source_id=url or title[:80],
            title=title,
            authors=authors,
            year=year,
            doi=doi,
            abstract=content if len(content) > 50 else None,
            url=url,
            paper_type=paper_type,
            raw_metadata={
                "engine": r.get("engine", ""),
                "engines": r.get("engines", []),
                "score": r.get("score", 0),
                "category": category,
                "position": r.get("positions", []),
            },
        )

    def _serialize_result(self, result: SearchResult) -> dict:
        """Serialize SearchResult for caching."""
        return {
            "source": result.source,
            "total_results": result.total_results,
            "has_more": result.has_more,
            "papers": [
                {
                    "source": p.source,
                    "source_id": p.source_id,
                    "title": p.title,
                    "authors": p.authors,
                    "year": p.year,
                    "doi": p.doi,
                    "abstract": p.abstract,
                    "venue": p.venue,
                    "url": p.url,
                    "citation_count": p.citation_count,
                    "paper_type": p.paper_type,
                    "raw_metadata": p.raw_metadata,
                }
                for p in result.papers
            ],
        }

    def _deserialize_result(self, data: dict, query: SearchQuery) -> SearchResult:
        """Deserialize cached data back to SearchResult."""
        papers = [
            RawPaper(
                source=p["source"],
                source_id=p["source_id"],
                title=p["title"],
                authors=p.get("authors", []),
                year=p.get("year"),
                doi=p.get("doi"),
                abstract=p.get("abstract"),
                venue=p.get("venue"),
                url=p.get("url"),
                citation_count=p.get("citation_count"),
                paper_type=p.get("paper_type"),
                raw_metadata=p.get("raw_metadata", {}),
            )
            for p in data.get("papers", [])
        ]
        return SearchResult(
            source=data.get("source", "searxng"),
            query=query,
            papers=papers,
            total_results=data.get("total_results", 0),
            has_more=data.get("has_more", False),
        )
