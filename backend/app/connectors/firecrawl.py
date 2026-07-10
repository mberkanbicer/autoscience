"""Firecrawl web search connector."""

from typing import Any

import httpx
import structlog

from app.services.cache_service import CacheService

from .base import AcademicConnector, RawPaper, SearchQuery, SearchResult, create_connector_client

logger = structlog.get_logger()


class FirecrawlConnector(AcademicConnector):
    """Connector for Firecrawl API to search and scrape the web.
    
    This acts as a bridge to allow our academic system to gather context
    from the general web (e.g. news, general info, documentation) in markdown.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.firecrawl.dev/v1",
        cache_service: CacheService | None = None,
        cache_ttl: int = 86400,  # 24h default for web content
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self.cache = cache_service
        self.cache_ttl = cache_ttl

    @property
    def connector_name(self) -> str:
        return "firecrawl"

    @property
    def base_url(self) -> str:
        return self._base_url

    async def search(self, query: SearchQuery, force_refresh: bool = False) -> SearchResult:
        """Search the web using Firecrawl and get markdown content."""
        if not self._api_key:
            logger.warning("firecrawl_search_failed", reason="No API key provided")
            return SearchResult(source=self.connector_name, query=query, papers=[], total_results=0)

        # Check cache
        cache_kwargs = {
            "text": query.text,
            "limit": query.limit,
        }

        if self.cache:
            cached, hit = await self.cache.get(
                "firecrawl", force_refresh=force_refresh, **cache_kwargs,
            )
            if hit and cached:
                return self._deserialize_result(cached, query)

        papers = []
        try:
            # Note: Firecrawl API docs say the /search endpoint accepts a POST request
            url = f"{self.base_url}/search"
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "query": query.text,
                "limit": min(query.limit, 10), # Firecrawl usually has lower limits per search
                "scrapeOptions": {
                    "formats": ["markdown"],
                },
            }

            async with create_connector_client(timeout=httpx.Timeout(60.0)) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

            raw_results = data.get("data", [])
            for item in raw_results:
                paper = self._result_to_paper(item)
                if paper:
                    papers.append(paper)

            logger.info("firecrawl_search_completed", query=query.text, count=len(papers))

        except httpx.HTTPStatusError as e:
            logger.error("firecrawl_search_http_error", status=e.response.status_code, error=e.response.text[:500], query=query.text)
        except httpx.RequestError as e:
            logger.warning("firecrawl_search_network_error", error=str(e), query=query.text)
        except Exception as e:
            logger.error("firecrawl_search_failed", error=str(e), query=query.text, exc_info=True)

        result = SearchResult(
            source=self.connector_name,
            query=query,
            papers=papers,
            total_results=len(papers),
            has_more=False,
        )

        # Cache result
        if self.cache and papers:
            try:
                serialized = self._serialize_result(result)
                await self.cache.set(
                    "firecrawl", serialized, ttl_seconds=self.cache_ttl, **cache_kwargs,
                )
            except Exception as e:
                logger.warning("firecrawl_cache_set_failed", error=str(e), exc_info=True)

        return result

    async def get_paper(self, identifier: str) -> RawPaper | None:
        """Fetch a specific URL via Firecrawl scrape endpoint.
        
        For Firecrawl, identifier is the URL.
        """
        if not self._api_key or not identifier.startswith("http"):
            return None

        try:
            url = f"{self.base_url}/scrape"
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "url": identifier,
                "formats": ["markdown"],
            }

            async with create_connector_client(timeout=httpx.Timeout(60.0)) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

            return self._result_to_paper(data.get("data", {}))
        except httpx.HTTPStatusError as e:
            logger.error("firecrawl_scrape_http_error", url=identifier, status=e.response.status_code, error=e.response.text[:500])
            return None
        except httpx.RequestError as e:
            logger.warning("firecrawl_scrape_network_error", url=identifier, error=str(e))
            return None
        except Exception as e:
            logger.error("firecrawl_scrape_failed", url=identifier, error=str(e), exc_info=True)
            return None

    async def get_citations(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        return []

    async def get_references(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        return []

    def _result_to_paper(self, item: dict[str, Any]) -> RawPaper | None:
        if not item:
            return None

        title = item.get("title") or item.get("metadata", {}).get("title") or "Unknown Web Page"
        url = item.get("url", "")
        if not url:
            return None

        content = item.get("markdown", "")
        # Use description/snippet as abstract if present, else first part of markdown
        abstract = item.get("metadata", {}).get("description")
        if not abstract and content:
            abstract = content[:500] + "..." if len(content) > 500 else content

        return RawPaper(
            source=self.connector_name,
            source_id=url,
            title=title,
            abstract=abstract,
            url=url,
            paper_type="web",
            raw_metadata={"markdown": content, "metadata": item.get("metadata", {})},
        )

    def _serialize_result(self, result: SearchResult) -> dict:
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
            source=data.get("source", "firecrawl"),
            query=query,
            papers=papers,
            total_results=data.get("total_results", 0),
            has_more=data.get("has_more", False),
        )
