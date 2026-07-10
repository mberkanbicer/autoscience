"""Crossref academic source connector."""

import json
from typing import Any

import httpx
import structlog

from .base import AcademicConnector, RawPaper, SearchQuery, SearchResult, create_connector_client

logger = structlog.get_logger()


class CrossrefConnector(AcademicConnector):
    """Connector for Crossref API (free, no API key required)."""

    BASE_URL = "https://api.crossref.org"

    def __init__(self, email: str | None = None):
        """Initialize Crossref connector.

        Args:
            email: Optional email for polite API access.

        """
        self.email = email
        headers = {"User-Agent": f"autoscience/0.1 (mailto:{email})" if email else "autoscience/0.1"}

        self.client = create_connector_client(
            base_url=self.BASE_URL,
            headers=headers,
        )

    @property
    def connector_name(self) -> str:
        return "crossref"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    async def search(self, query: SearchQuery) -> SearchResult:
        """Search for papers using Crossref API."""
        params: dict[str, Any] = {
            "query": query.text,
            "rows": query.limit,
            "sort": self._get_sort_param(query.sort_by),
            "order": "desc",
        }

        # Add filters
        filters = []
        if query.year_from:
            filters.append(f"from-pub-date:{query.year_from}")
        if query.year_to:
            filters.append(f"until-pub-date:{query.year_to}")
        if query.paper_type:
            type_map = {
                "journal-article": "journal-article",
                "proceedings-article": "proceedings-article",
                "book-chapter": "book-chapter",
            }
            if query.paper_type in type_map:
                filters.append(f"type:{type_map[query.paper_type]}")

        if filters:
            params["filter"] = ",".join(filters)

        try:
            response = await self.client.get("/works", params=params)
            response.raise_for_status()
            data = response.json()

            papers = []
            for item in data.get("message", {}).get("items", []):
                paper = self._parse_work(item)
                if paper:
                    papers.append(paper)

            total = data.get("message", {}).get("total-results", 0)

            return SearchResult(
                source=self.connector_name,
                query=query,
                papers=papers,
                total_results=total,
                has_more=len(papers) < total,
            )

        except httpx.HTTPStatusError as e:
            logger.error("crossref_search_http_error", status_code=e.response.status_code, query=query.text)
            raise
        except httpx.TimeoutException:
            logger.error("crossref_search_timeout", query=query.text)
            raise
        except httpx.RequestError as e:
            logger.error("crossref_search_request_failed", error=str(e), query=query.text)
            raise
        except json.JSONDecodeError as e:
            logger.error("crossref_search_json_failed", error=str(e), query=query.text)
            raise

    async def get_paper(self, identifier: str) -> RawPaper | None:
        """Get a paper by DOI."""
        try:
            response = await self.client.get(f"/works/{identifier}")

            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json()

            return self._parse_work(data.get("message", {}))

        except httpx.HTTPStatusError as e:
            logger.error("crossref_get_paper_http_error", status_code=e.response.status_code, identifier=identifier)
            raise
        except httpx.TimeoutException:
            logger.error("crossref_get_paper_timeout", identifier=identifier)
            raise
        except httpx.RequestError as e:
            logger.error("crossref_get_paper_request_failed", error=str(e), identifier=identifier)
            raise
        except json.JSONDecodeError as e:
            logger.error("crossref_get_paper_json_failed", error=str(e), identifier=identifier)
            raise

    async def get_citations(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers that cite this paper (uses relation API)."""
        params = {
            "filter": "relation-type:is-referenced-by",
            "rows": limit,
            "sort": "is-referenced-by-count",
            "order": "desc",
        }

        try:
            # Crossref doesn't have a direct citations endpoint
            # We search for papers that reference this DOI
            response = await self.client.get(
                "/works",
                params={**params, "query.bibliographic": paper_id},
            )
            response.raise_for_status()
            data = response.json()

            papers = []
            for item in data.get("message", {}).get("items", []):
                paper = self._parse_work(item)
                if paper:
                    papers.append(paper)

            return papers

        except httpx.HTTPStatusError as e:
            logger.error("crossref_citations_http_error", status_code=e.response.status_code, paper_id=paper_id)
            raise
        except httpx.TimeoutException:
            logger.error("crossref_citations_timeout", paper_id=paper_id)
            raise
        except httpx.RequestError as e:
            logger.error("crossref_citations_request_failed", error=str(e), paper_id=paper_id)
            raise
        except json.JSONDecodeError as e:
            logger.error("crossref_citations_json_failed", error=str(e), paper_id=paper_id)
            raise

    async def get_references(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers referenced by this paper."""
        try:
            # Get the paper's reference list
            response = await self.client.get(f"/works/{paper_id}")
            response.raise_for_status()
            data = response.json()

            work = data.get("message", {})
            references = work.get("reference", [])[:limit]

            # Get full details for each reference
            papers = []
            for ref in references:
                doi = ref.get("DOI")
                if doi:
                    paper = await self.get_paper(doi)
                    if paper:
                        papers.append(paper)

            return papers

        except httpx.HTTPStatusError as e:
            logger.error("crossref_references_http_error", status_code=e.response.status_code, paper_id=paper_id)
            raise
        except httpx.TimeoutException:
            logger.error("crossref_references_timeout", paper_id=paper_id)
            raise
        except httpx.RequestError as e:
            logger.error("crossref_references_request_failed", error=str(e), paper_id=paper_id)
            raise
        except json.JSONDecodeError as e:
            logger.error("crossref_references_json_failed", error=str(e), paper_id=paper_id)
            raise

    async def get_similar_works(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get similar works based on subject and type."""
        try:
            # Get the paper first
            paper = await self.get_paper(paper_id)
            if not paper:
                return []

            # Search based on title and venue
            query = SearchQuery(
                text=paper.title,
                year_from=paper.year - 2 if paper.year else None,
                year_to=paper.year + 2 if paper.year else None,
                limit=limit,
            )
            result = await self.search(query)

            # Filter out the original paper
            return [p for p in result.papers if p.source_id != paper_id]

        except httpx.HTTPStatusError as e:
            logger.error("crossref_similar_http_error", status_code=e.response.status_code, paper_id=paper_id)
            return []
        except httpx.TimeoutException:
            logger.error("crossref_similar_timeout", paper_id=paper_id)
            return []
        except httpx.RequestError as e:
            logger.error("crossref_similar_request_failed", error=str(e), paper_id=paper_id)
            return []
        except json.JSONDecodeError as e:
            logger.error("crossref_similar_json_failed", error=str(e), paper_id=paper_id)
            return []

    def _get_sort_param(self, sort_by: str) -> str:
        """Convert sort_by to Crossref API parameter."""
        sort_map = {
            "relevance": "relevance",
            "citations": "is-referenced-by-count",
            "date": "deposited",
        }
        return sort_map.get(sort_by, "relevance")

    def _parse_work(self, work: dict[str, Any]) -> RawPaper | None:
        """Parse a Crossref work object into a RawPaper."""
        try:
            if not work:
                return None

            # Extract title
            title_list = work.get("title", [])
            title = title_list[0] if title_list else ""
            if not title:
                return None

            # Extract authors
            authors = []
            for author in work.get("author", []):
                given = author.get("given", "")
                family = author.get("family", "")
                name = f"{given} {family}".strip()
                if name:
                    authors.append(name)

            # Extract year
            year = None
            published = work.get("published-print", {}) or work.get("published-online", {})
            date_parts = published.get("date-parts", [[]])
            if date_parts and date_parts[0]:
                year = date_parts[0][0]

            # Extract DOI
            doi = work.get("DOI")

            # Extract venue
            venue = None
            container = work.get("container-title", [])
            if container:
                venue = container[0]

            # Determine paper type
            paper_type = None
            type_map = {
                "journal-article": "research",
                "proceedings-article": "research",
                "book-chapter": "research",
                "review": "review",
                "dataset": "dataset",
            }
            work_type = work.get("type")
            if work_type in type_map:
                paper_type = type_map[work_type]

            # Extract abstract
            abstract = work.get("abstract")
            if abstract:
                # Remove HTML tags
                import re
                abstract = re.sub(r"<[^>]+>", "", abstract)

            return RawPaper(
                source=self.connector_name,
                source_id=work.get("URL", ""),
                title=title,
                authors=authors,
                year=year,
                doi=doi,
                abstract=abstract,
                venue=venue,
                url=work.get("URL"),
                citation_count=work.get("is-referenced-by-count"),
                paper_type=paper_type,
                raw_metadata=work,
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.error("crossref_parse_failed", error=str(e))
            return None

    async def health_check(self) -> bool:
        """Check if Crossref API is accessible."""
        try:
            response = await self.client.get("/works?rows=1")
            return response.status_code == 200
        except httpx.RequestError:
            return False
