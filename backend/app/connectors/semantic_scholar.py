"""Semantic Scholar academic source connector."""

import httpx
import structlog
from typing import Any

from .base import AcademicConnector, RawPaper, SearchQuery, SearchResult

logger = structlog.get_logger()


class SemanticScholarConnector(AcademicConnector):
    """Connector for Semantic Scholar API."""

    BASE_URL = "https://api.semanticscholar.org"

    def __init__(self, api_key: str | None = None):
        """
        Initialize Semantic Scholar connector.

        Args:
            api_key: Optional API key for higher rate limits.
        """
        self.api_key = api_key
        headers = {"User-Agent": "autoscience/0.1"}
        if api_key:
            headers["x-api-key"] = api_key

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers=headers,
        )

    @property
    def connector_name(self) -> str:
        return "semantic_scholar"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    async def search(self, query: SearchQuery) -> SearchResult:
        """Search for papers using Semantic Scholar API."""
        params: dict[str, Any] = {
            "query": query.text,
            "limit": query.limit,
            "fields": "paperId,externalIds,title,authors,year,abstract,venue,citationCount,publicationTypes,referenceCount",
        }

        # Add year filter
        if query.year_from or query.year_to:
            year_range = ""
            if query.year_from:
                year_range += f"{query.year_from}-"
            if query.year_to:
                year_range += str(query.year_to)
            params["year"] = year_range

        try:
            response = await self.client.get("/graph/v1/paper/search", params=params)
            response.raise_for_status()
            data = response.json()

            papers = []
            for paper_data in data.get("data", []):
                paper = self._parse_paper(paper_data)
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

        except Exception as e:
            logger.error("semantic_scholar_search_failed", error=str(e), query=query.text)
            raise

    async def get_paper(self, identifier: str) -> RawPaper | None:
        """Get a paper by DOI, PMID, or Semantic Scholar ID."""
        # Determine ID type
        if identifier.startswith("10."):
            # DOI
            id_type = "DOI"
            id_value = identifier
        elif identifier.startswith("PMID:"):
            id_type = "PMID"
            id_value = identifier[5:]
        elif identifier.startswith("ARXIV:"):
            id_type = "ARXIV"
            id_value = identifier[6:]
        else:
            # Assume Semantic Scholar ID
            id_type = "S2_ID"
            id_value = identifier

        params = {
            "fields": "paperId,externalIds,title,authors,year,abstract,venue,citationCount,publicationTypes,referenceCount,references",
        }

        try:
            response = await self.client.get(
                f"/graph/v1/paper/{id_type}:{id_value}",
                params=params,
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()
            return self._parse_paper(response.json())

        except Exception as e:
            logger.error("semantic_scholar_get_paper_failed", error=str(e), identifier=identifier)
            raise

    async def get_citations(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers that cite this paper."""
        params = {
            "fields": "paperId,externalIds,title,authors,year,abstract,venue,citationCount,publicationTypes",
            "limit": min(limit, 100),
        }

        try:
            response = await self.client.get(
                f"/graph/v1/paper/{paper_id}/citations",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            papers = []
            for item in data.get("data", [])[:limit]:
                citing_paper = item.get("citingPaper", {})
                paper = self._parse_paper(citing_paper)
                if paper:
                    papers.append(paper)

            return papers

        except Exception as e:
            logger.error("semantic_scholar_citations_failed", error=str(e), paper_id=paper_id)
            raise

    async def get_references(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers referenced by this paper."""
        params = {
            "fields": "paperId,externalIds,title,authors,year,abstract,venue,citationCount,publicationTypes",
            "limit": min(limit, 100),
        }

        try:
            response = await self.client.get(
                f"/graph/v1/paper/{paper_id}/references",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            papers = []
            for item in data.get("data", [])[:limit]:
                cited_paper = item.get("citedPaper", {})
                paper = self._parse_paper(cited_paper)
                if paper:
                    papers.append(paper)

            return papers

        except Exception as e:
            logger.error("semantic_scholar_references_failed", error=str(e), paper_id=paper_id)
            raise

    async def get_paper_batch(self, paper_ids: list[str], batch_size: int = 100) -> list[RawPaper]:
        """Get multiple papers in batch."""
        papers = []

        for i in range(0, len(paper_ids), batch_size):
            batch = paper_ids[i : i + batch_size]
            params = {
                "ids": batch,
                "fields": "paperId,externalIds,title,authors,year,abstract,venue,citationCount,publicationTypes",
            }

            try:
                response = await self.client.post(
                    "/graph/v1/paper/batch",
                    json=params,
                )
                response.raise_for_status()
                data = response.json()

                for paper_data in data:
                    if paper_data:  # Can be null for invalid IDs
                        paper = self._parse_paper(paper_data)
                        if paper:
                            papers.append(paper)

            except Exception as e:
                logger.error("semantic_scholar_batch_failed", error=str(e))
                continue

        return papers

    def _parse_paper(self, data: dict[str, Any]) -> RawPaper | None:
        """Parse a Semantic Scholar paper object into a RawPaper."""
        try:
            if not data or not data.get("title"):
                return None

            # Extract authors
            authors = []
            for author in data.get("authors", []):
                name = author.get("name")
                if name:
                    authors.append(name)

            # Extract external IDs
            external_ids = data.get("externalIds", {})
            doi = external_ids.get("DOI")

            # Determine paper type
            paper_type = None
            pub_types = data.get("publicationTypes", [])
            if pub_types:
                type_map = {
                    "JournalArticle": "research",
                    "Review": "review",
                    "Conference": "research",
                    "Book": "research",
                    "Dataset": "dataset",
                }
                for pt in pub_types:
                    if pt in type_map:
                        paper_type = type_map[pt]
                        break

            # Extract references
            references = []
            for ref in data.get("references", []) or []:
                ref_id = ref.get("paperId")
                if ref_id:
                    references.append(ref_id)

            return RawPaper(
                source=self.connector_name,
                source_id=data.get("paperId", ""),
                title=data.get("title", ""),
                authors=authors,
                year=data.get("year"),
                doi=doi,
                abstract=data.get("abstract"),
                venue=data.get("venue"),
                url=f"https://www.semanticscholar.org/paper/{data.get('paperId', '')}",
                citation_count=data.get("citationCount"),
                paper_type=paper_type,
                references=references,
                raw_metadata=data,
            )

        except Exception as e:
            logger.error("semantic_scholar_parse_failed", error=str(e))
            return None

    async def health_check(self) -> bool:
        """Check if Semantic Scholar API is accessible."""
        try:
            response = await self.client.get("/graph/v1/paper/search?query=test&limit=1")
            return response.status_code == 200
        except Exception:
            return False
