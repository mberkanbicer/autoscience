"""DOAJ (Directory of Open Access Journals) academic source connector."""

import json
from typing import Any

import httpx
import structlog

from .base import AcademicConnector, RawPaper, SearchQuery, SearchResult, create_connector_client

logger = structlog.get_logger()


class DOAJConnector(AcademicConnector):
    """Connector for DOAJ API (free, no API key required)."""

    BASE_URL = "https://doaj.org/api/v3"

    def __init__(self):
        """Initialize DOAJ connector."""
        self.client = create_connector_client(
            base_url=self.BASE_URL,
            headers={"User-Agent": "autoscience/0.1"},
        )

    @property
    def connector_name(self) -> str:
        return "doaj"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    async def search(self, query: SearchQuery) -> SearchResult:
        """Search for papers using DOAJ API."""
        params: dict[str, Any] = {
            "query": query.text,
            "page": 1,
            "pageSize": query.limit,
            "sort": self._get_sort_param(query.sort_by),
        }

        # Add year filter
        filters = []
        if query.year_from:
            filters.append(f"year:{query.year_from}-{query.year_to or 2099}")
        if query.year_to and not query.year_from:
            filters.append(f"year:1970-{query.year_to}")

        if filters:
            params["filter"] = ",".join(filters)

        try:
            response = await self.client.get("/search/articles", params=params)
            response.raise_for_status()
            data = response.json()

            papers = []
            for result in data.get("results", []):
                paper = self._parse_article(result)
                if paper:
                    papers.append(paper)

            total = data.get("total", 0)

            return SearchResult(
                source=self.connector_name,
                query=query,
                papers=papers,
                total_results=total,
                has_more=len(papers) < total,
            )

        except httpx.HTTPStatusError as e:
            logger.error("doaj_search_http_error", status_code=e.response.status_code, query=query.text)
            raise
        except httpx.TimeoutException:
            logger.error("doaj_search_timeout", query=query.text)
            raise
        except httpx.RequestError as e:
            logger.error("doaj_search_request_failed", error=str(e), query=query.text)
            raise
        except json.JSONDecodeError as e:
            logger.error("doaj_search_json_failed", error=str(e), query=query.text)
            raise

    async def get_paper(self, identifier: str) -> RawPaper | None:
        """Get a paper by DOI or DOAJ article ID."""
        try:
            # DOAJ API supports search by DOI
            params = {
                "query": f'doi:"{identifier}"',
                "pageSize": 1,
            }
            response = await self.client.get("/search/articles", params=params)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return None

            return self._parse_article(results[0])

        except httpx.HTTPStatusError as e:
            logger.error("doaj_get_paper_http_error", status_code=e.response.status_code, identifier=identifier)
            raise
        except httpx.TimeoutException:
            logger.error("doaj_get_paper_timeout", identifier=identifier)
            raise
        except httpx.RequestError as e:
            logger.error("doaj_get_paper_request_failed", error=str(e), identifier=identifier)
            raise
        except json.JSONDecodeError as e:
            logger.error("doaj_get_paper_json_failed", error=str(e), identifier=identifier)
            raise

    async def get_citations(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers that cite this paper (not supported by DOAJ API)."""
        logger.info("doaj_citations_not_supported", paper_id=paper_id)
        return []

    async def get_references(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers referenced by this paper (not supported by DOAJ API)."""
        logger.info("doaj_references_not_supported", paper_id=paper_id)
        return []

    def _get_sort_param(self, sort_by: str) -> str:
        """Convert sort_by to DOAJ API parameter."""
        sort_map = {
            "relevance": "relevance",
            "citations": "references",
            "date": "created_date",
        }
        return sort_map.get(sort_by, "relevance")

    def _parse_article(self, data: dict[str, Any]) -> RawPaper | None:
        """Parse a DOAJ article object into a RawPaper."""
        try:
            if not data:
                return None

            bibjson = data.get("bibjson", {})

            # Extract title
            title = bibjson.get("title", "")
            if not title:
                return None

            # Extract authors
            authors = []
            for author in bibjson.get("author", []):
                name = author.get("name", "")
                if name:
                    authors.append(name)

            # Extract year
            year = None
            year_str = bibjson.get("year")
            if year_str:
                try:
                    year = int(year_str)
                except (ValueError, TypeError):
                    pass

            identifier = data.get("id", "")

            # Extract DOI
            doi = None
            for ident in bibjson.get("identifier", []):
                if ident.get("type") == "doi":
                    doi = ident.get("id")
                    break

            # Extract abstract
            abstract = None
            sections = []
            for section in bibjson.get("abstract", []):
                if isinstance(section, str):
                    sections.append(section)
                elif isinstance(section, dict):
                    sections.append(section.get("text", ""))
            if sections:
                abstract = " ".join(sections)

            # Extract journal/venue
            venue = bibjson.get("journal", {}).get("title") or bibjson.get("journal", {}).get("name")

            # Extract URLs
            url = None
            for link in bibjson.get("link", []):
                if link.get("type") == "fulltext":
                    url = link.get("url")
                    break
            if not url:
                for link in bibjson.get("link", []):
                    url = link.get("url")
                    if url:
                        break

            # Determine paper type (DOAJ is all open access journals)
            paper_type = "research"

            return RawPaper(
                source=self.connector_name,
                source_id=identifier,
                title=title,
                authors=authors,
                year=year,
                doi=doi,
                abstract=abstract,
                venue=venue,
                url=url,
                citation_count=None,
                paper_type=paper_type,
                raw_metadata=data,
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.error("doaj_parse_failed", error=str(e))
            return None

    async def health_check(self) -> bool:
        """Check if DOAJ API is accessible."""
        try:
            response = await self.client.get("/search/articles?query=test&pageSize=1")
            return response.status_code == 200
        except httpx.RequestError:
            return False
