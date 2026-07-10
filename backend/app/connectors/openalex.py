"""OpenAlex academic source connector."""

import json
from typing import Any

import httpx
import structlog

from .base import AcademicConnector, RawPaper, SearchQuery, SearchResult, create_connector_client

logger = structlog.get_logger()


class OpenAlexConnector(AcademicConnector):
    """Connector for OpenAlex API (free, no API key required)."""

    BASE_URL = "https://api.openalex.org"

    def __init__(self, email: str | None = None):
        """Initialize OpenAlex connector.

        Args:
            email: Optional email for polite API access (faster rate limits).

        """
        self.email = email
        self.client = create_connector_client(
            base_url=self.BASE_URL,
            headers={"User-Agent": f"autoscience/0.1 ({email})" if email else "autoscience/0.1"},
        )

    @property
    def connector_name(self) -> str:
        return "openalex"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    async def search(self, query: SearchQuery) -> SearchResult:
        """Search for papers using OpenAlex API."""
        params: dict[str, Any] = {
            "search": query.text,
            "per_page": query.limit,
        }

        # Add filters
        filters = []
        if query.year_from or query.year_to:
            year_filter = ""
            if query.year_from and query.year_to:
                year_filter = f"{query.year_from}-{query.year_to}"
            elif query.year_from:
                year_filter = f"{query.year_from}-"
            elif query.year_to:
                year_filter = f"-{query.year_to}"
            filters.append(f"publication_year:{year_filter}")

        if query.paper_type:
            type_map = {
                "research": "article",
                "review": "review",
                "survey": "review",
            }
            if query.paper_type in type_map:
                filters.append(f"type:{type_map[query.paper_type]}")

        if filters:
            params["filter"] = ",".join(filters)

        # Sorting
        sort_map = {
            "relevance": "relevance_score:desc",
            "citations": "cited_by_count:desc",
            "date": "publication_date:desc",
        }
        if query.sort_by in sort_map:
            params["sort"] = sort_map[query.sort_by]

        try:
            response = await self.client.get("/works", params=params)
            response.raise_for_status()
            data = response.json()

            papers = []
            for work in data.get("results", []):
                paper = self._parse_work(work)
                if paper:
                    papers.append(paper)

            return SearchResult(
                source=self.connector_name,
                query=query,
                papers=papers,
                total_results=data.get("meta", {}).get("count", 0),
                has_more=len(papers) < data.get("meta", {}).get("count", 0),
            )

        except httpx.HTTPStatusError as e:
            logger.error("openalex_search_http_error", status_code=e.response.status_code, query=query.text)
            raise
        except httpx.TimeoutException:
            logger.error("openalex_search_timeout", query=query.text)
            raise
        except httpx.RequestError as e:
            logger.error("openalex_search_request_failed", error=str(e), query=query.text)
            raise
        except json.JSONDecodeError as e:
            logger.error("openalex_search_json_failed", error=str(e), query=query.text)
            raise

    async def get_paper(self, identifier: str) -> RawPaper | None:
        """Get a paper by DOI or OpenAlex ID."""
        try:
            if identifier.startswith("10."):
                # DOI
                response = await self.client.get(f"/works/doi:{identifier}")
            else:
                # OpenAlex ID
                response = await self.client.get(f"/works/{identifier}")

            if response.status_code == 404:
                return None

            response.raise_for_status()
            return self._parse_work(response.json())

        except httpx.HTTPStatusError as e:
            logger.error("openalex_get_paper_http_error", status_code=e.response.status_code, identifier=identifier)
            raise
        except httpx.TimeoutException:
            logger.error("openalex_get_paper_timeout", identifier=identifier)
            raise
        except httpx.RequestError as e:
            logger.error("openalex_get_paper_request_failed", error=str(e), identifier=identifier)
            raise
        except json.JSONDecodeError as e:
            logger.error("openalex_get_paper_json_failed", error=str(e), identifier=identifier)
            raise

    async def get_citations(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers that cite this paper."""
        params = {
            "filter": f"cites:{paper_id}",
            "per_page": limit,
            "sort": "cited_by_count:desc",
        }

        try:
            response = await self.client.get("/works", params=params)
            response.raise_for_status()
            data = response.json()

            papers = []
            for work in data.get("results", []):
                paper = self._parse_work(work)
                if paper:
                    papers.append(paper)

            return papers

        except httpx.HTTPStatusError as e:
            logger.error("openalex_citations_http_error", status_code=e.response.status_code, paper_id=paper_id)
            raise
        except httpx.TimeoutException:
            logger.error("openalex_citations_timeout", paper_id=paper_id)
            raise
        except httpx.RequestError as e:
            logger.error("openalex_citations_request_failed", error=str(e), paper_id=paper_id)
            raise
        except json.JSONDecodeError as e:
            logger.error("openalex_citations_json_failed", error=str(e), paper_id=paper_id)
            raise

    async def get_references(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers referenced by this paper."""
        params = {
            "filter": f"cited_by:{paper_id}",
            "per_page": limit,
            "sort": "cited_by_count:desc",
        }

        try:
            response = await self.client.get("/works", params=params)
            response.raise_for_status()
            data = response.json()

            papers = []
            for work in data.get("results", []):
                paper = self._parse_work(work)
                if paper:
                    papers.append(paper)

            return papers

        except httpx.HTTPStatusError as e:
            logger.error("openalex_references_http_error", status_code=e.response.status_code, paper_id=paper_id)
            raise
        except httpx.TimeoutException:
            logger.error("openalex_references_timeout", paper_id=paper_id)
            raise
        except httpx.RequestError as e:
            logger.error("openalex_references_request_failed", error=str(e), paper_id=paper_id)
            raise
        except json.JSONDecodeError as e:
            logger.error("openalex_references_json_failed", error=str(e), paper_id=paper_id)
            raise

    def _parse_work(self, work: dict[str, Any]) -> RawPaper | None:
        """Parse an OpenAlex work object into a RawPaper."""
        try:
            # Extract authors
            authors = []
            for authorship in work.get("authorships", []):
                author = authorship.get("author", {})
                name = author.get("display_name")
                if name:
                    authors.append(name)

            # Extract DOI
            doi = work.get("doi")
            if doi:
                doi = doi.replace("https://doi.org/", "")

            # Determine paper type
            paper_type = None
            work_type = work.get("type")
            if work_type:
                type_map = {
                    "article": "research",
                    "review": "review",
                    "book-chapter": "research",
                    "dataset": "dataset",
                }
                paper_type = type_map.get(work_type)

            # Extract venue
            venue = None
            primary_location = work.get("primary_location", {})
            if primary_location:
                source = primary_location.get("source", {})
                venue = source.get("display_name")

            return RawPaper(
                source=self.connector_name,
                source_id=work.get("id", ""),
                title=work.get("title", ""),
                authors=authors,
                year=work.get("publication_year"),
                doi=doi,
                abstract=self._reconstruct_abstract(work.get("abstract_inverted_index")),
                venue=venue,
                url=work.get("id"),
                citation_count=work.get("cited_by_count"),
                paper_type=paper_type,
                raw_metadata=work,
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.error("openalex_parse_failed", error=str(e))
            return None

    def _reconstruct_abstract(self, inverted_index: dict[str, list[int]] | None) -> str | None:
        """Reconstruct abstract from OpenAlex inverted index format."""
        if not inverted_index:
            return None

        try:
            # Create list of (word, position) pairs
            word_positions = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    word_positions.append((word, pos))

            # Sort by position
            word_positions.sort(key=lambda x: x[1])

            # Join words
            return " ".join(word for word, _ in word_positions)

        except (KeyError, TypeError, ValueError):
            return None

    async def health_check(self) -> bool:
        """Check if OpenAlex API is accessible."""
        try:
            response = await self.client.get("/works?per_page=1")
            return response.status_code == 200
        except httpx.RequestError:
            return False
