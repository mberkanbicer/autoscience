"""Unpaywall academic source connector."""

import json
from typing import Any

import httpx
import structlog

from .base import AcademicConnector, RawPaper, SearchQuery, SearchResult, create_connector_client

logger = structlog.get_logger()


class UnpaywallConnector(AcademicConnector):
    """Connector for Unpaywall API (free with email registration)."""

    BASE_URL = "https://api.unpaywall.org/v2"

    def __init__(self, email: str | None = None):
        """Initialize Unpaywall connector.

        Args:
            email: Required email for API access (identifies you to the API).

        """
        self.email = email
        self.client = create_connector_client()
        self._configured = email is not None and "@" in email

    @property
    def connector_name(self) -> str:
        return "unpaywall"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    @property
    def is_configured(self) -> bool:
        return self._configured

    async def search(self, query: SearchQuery) -> SearchResult:
        """Search for papers using Unpaywall API.

        Note: Unpaywall is primarily a DOI-based lookup service, not a full
        search engine. This implementation returns empty results for general
        search queries, as Unpaywall does not provide a search endpoint.
        """
        logger.info("unpaywall_search_not_supported", query=query.text)
        return SearchResult(
            source=self.connector_name,
            query=query,
            papers=[],
            total_results=0,
            has_more=False,
        )

    async def get_paper(self, identifier: str) -> RawPaper | None:
        """Get a paper by DOI (Unpaywall's primary interface)."""
        if not self._configured:
            logger.warning("unpaywall_not_configured")
            return None

        # Clean DOI
        doi = identifier.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
        if not doi.startswith("10."):
            return None

        params: dict[str, Any] = {"email": self.email}

        try:
            response = await self.client.get(
                f"{self.BASE_URL}/{doi}",
                params=params,
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json()
            return self._parse_response(data)

        except httpx.HTTPStatusError as e:
            logger.error("unpaywall_get_paper_http_error", status_code=e.response.status_code, identifier=identifier)
            return None
        except httpx.TimeoutException:
            logger.error("unpaywall_get_paper_timeout", identifier=identifier)
            return None
        except httpx.RequestError as e:
            logger.error("unpaywall_get_paper_request_failed", error=str(e), identifier=identifier)
            return None
        except json.JSONDecodeError as e:
            logger.error("unpaywall_get_paper_json_failed", error=str(e), identifier=identifier)
            return None

    async def get_citations(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers that cite this paper (not supported by Unpaywall)."""
        logger.info("unpaywall_citations_not_supported")
        return []

    async def get_references(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers referenced by this paper (not supported by Unpaywall)."""
        logger.info("unpaywall_references_not_supported")
        return []

    def _parse_response(self, data: dict[str, Any]) -> RawPaper | None:
        """Parse Unpaywall API response into a RawPaper."""
        try:
            if not data or not data.get("title"):
                return None

            title = data.get("title", "")
            doi = data.get("doi")
            year = data.get("year")

            # Extract authors
            authors = []
            for author in data.get("z_authors", []):
                given = author.get("given", "")
                family = author.get("family", "")
                name = f"{given} {family}".strip()
                if name:
                    authors.append(name)

            # Extract venue
            venue = data.get("journal_name") or data.get("publisher")

            # Extract abstract (Unpaywall doesn't provide abstracts directly)
            abstract = None

            # Determine paper type
            paper_type = data.get("genre", "research")
            type_map = {
                "journal-article": "research",
                "proceedings-article": "research",
                "book-chapter": "research",
                "review": "review",
                "dataset": "dataset",
            }
            paper_type = type_map.get(paper_type, "research")

            # Get best open access URL
            url = None
            best_location = data.get("best_oa_location", {}) or {}
            url = best_location.get("url_for_pdf") or best_location.get("url") or data.get("doi_url")

            # Get citation count if available
            citation_count = data.get("cited_by_count")

            return RawPaper(
                source=self.connector_name,
                source_id=doi or title[:50],
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
            logger.error("unpaywall_parse_failed", error=str(e))
            return None

    async def health_check(self) -> bool:
        """Check if Unpaywall API is accessible."""
        if not self._configured:
            return False
        try:
            # Test with a well-known DOI
            params = {"email": self.email}
            response = await self.client.get(
                f"{self.BASE_URL}/10.1038/nature12373",
                params=params,
            )
            return response.status_code == 200
        except httpx.RequestError:
            return False
