"""CORE academic source connector."""

import json
from typing import Any

import httpx
import structlog

from .base import AcademicConnector, RawPaper, SearchQuery, SearchResult, create_connector_client

logger = structlog.get_logger()


class COREConnector(AcademicConnector):
    """Connector for CORE API (requires free API key)."""

    BASE_URL = "https://api.core.ac.uk/v3"

    def __init__(self, api_key: str | None = None):
        """Initialize CORE connector.

        Args:
            api_key: CORE API key from https://core.ac.uk/services/api/.

        """
        self.api_key = api_key
        headers = {
            "User-Agent": "autoscience/0.1",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self.client = create_connector_client(
            base_url=self.BASE_URL,
            headers=headers,
        )
        self._configured = api_key is not None and len(api_key) > 0

    @property
    def connector_name(self) -> str:
        return "core"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    @property
    def is_configured(self) -> bool:
        """Returns True if an API key has been provided."""
        return self._configured

    async def search(self, query: SearchQuery) -> SearchResult:
        """Search for papers using CORE API."""
        if not self._configured:
            logger.warning("core_not_configured")
            return SearchResult(
                source=self.connector_name,
                query=query,
                papers=[],
                total_results=0,
                has_more=False,
            )

        params: dict[str, Any] = {
            "q": query.text,
            "limit": query.limit,
            "offset": 0,
        }

        if query.year_from:
            params["year"] = query.year_from

        try:
            response = await self.client.get("/search/outputs", params=params)
            response.raise_for_status()
            data = response.json()

            papers = []
            for result in data.get("results", []):
                paper = self._parse_output(result)
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
            logger.error("core_search_http_error", status_code=e.response.status_code, query=query.text)
            raise
        except httpx.TimeoutException:
            logger.error("core_search_timeout", query=query.text)
            raise
        except httpx.RequestError as e:
            logger.error("core_search_request_failed", error=str(e), query=query.text)
            raise
        except json.JSONDecodeError as e:
            logger.error("core_search_json_failed", error=str(e), query=query.text)
            raise

    async def get_paper(self, identifier: str) -> RawPaper | None:
        """Get a paper by DOI or CORE ID."""
        if not self._configured:
            logger.warning("core_not_configured")
            return None

        try:
            response = await self.client.get(f"/search/outputs?q={identifier}&limit=1")
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return None

            return self._parse_output(results[0])

        except httpx.HTTPStatusError as e:
            logger.error("core_get_paper_http_error", status_code=e.response.status_code, identifier=identifier)
            raise
        except httpx.TimeoutException:
            logger.error("core_get_paper_timeout", identifier=identifier)
            raise
        except httpx.RequestError as e:
            logger.error("core_get_paper_request_failed", error=str(e), identifier=identifier)
            raise
        except json.JSONDecodeError as e:
            logger.error("core_get_paper_json_failed", error=str(e), identifier=identifier)
            raise

    async def get_citations(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers that cite this paper."""
        if not self._configured:
            return []

        try:
            response = await self.client.get(
                f"/outputs/{paper_id}/citations",
                params={"limit": limit},
            )
            response.raise_for_status()
            data = response.json()

            return [
                paper
                for r in data.get("results", [])
                if (paper := self._parse_output(r)) is not None
            ]

        except httpx.HTTPStatusError as e:
            logger.error("core_citations_http_error", status_code=e.response.status_code, paper_id=paper_id)
            return []
        except httpx.TimeoutException:
            logger.error("core_citations_timeout", paper_id=paper_id)
            return []
        except httpx.RequestError as e:
            logger.error("core_citations_request_failed", error=str(e), paper_id=paper_id)
            return []
        except json.JSONDecodeError as e:
            logger.error("core_citations_json_failed", error=str(e), paper_id=paper_id)
            return []

    async def get_references(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers referenced by this paper."""
        if not self._configured:
            return []

        try:
            response = await self.client.get(
                f"/outputs/{paper_id}/references",
                params={"limit": limit},
            )
            response.raise_for_status()
            data = response.json()

            return [
                paper
                for r in data.get("results", [])
                if (paper := self._parse_output(r)) is not None
            ]

        except httpx.HTTPStatusError as e:
            logger.error("core_references_http_error", status_code=e.response.status_code, paper_id=paper_id)
            return []
        except httpx.TimeoutException:
            logger.error("core_references_timeout", paper_id=paper_id)
            return []
        except httpx.RequestError as e:
            logger.error("core_references_request_failed", error=str(e), paper_id=paper_id)
            return []
        except json.JSONDecodeError as e:
            logger.error("core_references_json_failed", error=str(e), paper_id=paper_id)
            return []

    def _parse_output(self, data: dict[str, Any]) -> RawPaper | None:
        """Parse a CORE output object into a RawPaper."""
        try:
            if not data or not data.get("title"):
                return None

            title = data.get("title", "")
            authors = [a.get("name", "") for a in data.get("authors", []) if a.get("name")]
            doi = data.get("doi")

            year = data.get("yearPublished") or data.get("datePublished")
            if year and isinstance(year, str):
                try:
                    year = int(year[:4])
                except (ValueError, TypeError):
                    year = None

            abstract = data.get("abstract")
            venue = data.get("journalName") or data.get("publisher")
            url = data.get("fullTextUrl") or data.get("sourceUrl")
            citation_count = data.get("citationCount")
            paper_type = "research"

            return RawPaper(
                source=self.connector_name,
                source_id=str(data.get("id", "")),
                title=title,
                authors=authors,
                year=year,
                doi=doi,
                abstract=abstract,
                venue=venue,
                url=url,
                citation_count=citation_count,
                paper_type=paper_type,
                raw_metadata=data,
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.error("core_parse_failed", error=str(e))
            return None

    async def health_check(self) -> bool:
        """Check if CORE API is accessible."""
        if not self._configured:
            return False
        try:
            response = await self.client.get("/search/outputs?q=test&limit=1")
            return response.status_code == 200
        except httpx.RequestError:
            return False
