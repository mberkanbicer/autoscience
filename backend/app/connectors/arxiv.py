"""arXiv academic source connector."""

import httpx
import structlog
from typing import Any
import xml.etree.ElementTree as ET

from .base import AcademicConnector, RawPaper, SearchQuery, SearchResult

logger = structlog.get_logger()


class ArxivConnector(AcademicConnector):
    """Connector for arXiv API (free, no API key required)."""

    BASE_URL = "http://export.arxiv.org/api/query"

    def __init__(self):
        """Initialize arXiv connector."""
        self.client = httpx.AsyncClient(timeout=30.0)

    @property
    def connector_name(self) -> str:
        return "arxiv"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    async def search(self, query: SearchQuery) -> SearchResult:
        """Search for papers using arXiv API."""
        # Build search query
        search_query = self._build_search_query(query)

        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": query.limit,
            "sortBy": self._get_sort_param(query.sort_by),
            "sortOrder": "descending",
        }

        try:
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()

            # Parse XML response
            papers, total = self._parse_response(response.text)

            return SearchResult(
                source=self.connector_name,
                query=query,
                papers=papers,
                total_results=total,
                has_more=len(papers) < total,
            )

        except Exception as e:
            logger.error("arxiv_search_failed", error=str(e), query=query.text)
            raise

    async def get_paper(self, identifier: str) -> RawPaper | None:
        """Get a paper by arXiv ID."""
        # Clean up arXiv ID
        if "arxiv.org" in identifier:
            # Extract ID from URL
            identifier = identifier.split("/")[-1]

        # Remove version suffix if present
        if identifier.endswith("v1") or identifier.endswith("v2") or identifier.endswith("v3"):
            identifier = identifier[:-2]

        params = {
            "id_list": identifier,
            "max_results": 1,
        }

        try:
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()

            papers, _ = self._parse_response(response.text)
            return papers[0] if papers else None

        except Exception as e:
            logger.error("arxiv_get_paper_failed", error=str(e), identifier=identifier)
            raise

    async def get_citations(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers that cite this paper (limited by arXiv API)."""
        # arXiv doesn't have a direct citations API
        # We search for papers that mention this arXiv ID
        query = SearchQuery(
            text=f"referenced by {paper_id}",
            limit=limit,
        )
        result = await self.search(query)
        return result.papers

    async def get_references(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers referenced by this paper."""
        # Get the paper first to extract references from abstract
        paper = await self.get_paper(paper_id)
        if not paper:
            return []

        # arXiv doesn't provide structured references
        # Return empty list as we can't reliably extract references
        return []

    async def get_recent(self, category: str = "cs.AI", limit: int = 20) -> list[RawPaper]:
        """Get recent papers from a category."""
        search_query = f"cat:{category}"
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": limit,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        try:
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()

            papers, _ = self._parse_response(response.text)
            return papers

        except Exception as e:
            logger.error("arxiv_recent_failed", error=str(e), category=category)
            return []

    def _build_search_query(self, query: SearchQuery) -> str:
        """Build arXiv search query string."""
        # arXiv uses specific query syntax
        parts = []

        # Title search
        parts.append(f"ti:{query.text}")

        # Year filter (arXiv doesn't directly support year filters in search)
        # We'll filter results after fetching

        return " AND ".join(parts) if parts else query.text

    def _get_sort_param(self, sort_by: str) -> str:
        """Convert sort_by to arXiv API parameter."""
        sort_map = {
            "relevance": "relevance",
            "citations": "relevance",  # arXiv doesn't have citation count sorting
            "date": "submittedDate",
        }
        return sort_map.get(sort_by, "relevance")

    def _parse_response(self, xml_content: str) -> tuple[list[RawPaper], int]:
        """Parse arXiv XML response."""
        papers = []

        try:
            root = ET.fromstring(xml_content)

            # Define namespaces
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "arxiv": "http://arxiv.org/schemas/atom",
            }

            # Get total results
            total = 0
            total_elem = root.find(".//{http://a9.com/-/spec/opensearch/1.1/}totalResults")
            if total_elem is not None and total_elem.text:
                total = int(total_elem.text)

            # Parse entries
            for entry in root.findall("atom:entry", ns):
                paper = self._parse_entry(entry, ns)
                if paper:
                    papers.append(paper)

        except Exception as e:
            logger.error("arxiv_parse_failed", error=str(e))

        return papers, total

    def _parse_entry(self, entry: ET.Element, ns: dict) -> RawPaper | None:
        """Parse an arXiv entry element."""
        try:
            # Extract title
            title_elem = entry.find("atom:title", ns)
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
            if not title:
                return None

            # Extract authors
            authors = []
            for author_elem in entry.findall("atom:author", ns):
                name_elem = author_elem.find("atom:name", ns)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text)

            # Extract abstract
            abstract_elem = entry.find("atom:summary", ns)
            abstract = abstract_elem.text.strip() if abstract_elem is not None and abstract_elem.text else None

            # Extract published date
            year = None
            published_elem = entry.find("atom:published", ns)
            if published_elem is not None and published_elem.text:
                year = int(published_elem.text[:4])

            # Extract arXiv ID
            id_elem = entry.find("atom:id", ns)
            arxiv_url = id_elem.text if id_elem is not None else ""
            arxiv_id = arxiv_url.split("/abs/")[-1] if "/abs/" in arxiv_url else ""

            # Extract DOI if available
            doi = None
            doi_elem = entry.find("arxiv:doi", ns)
            if doi_elem is not None and doi_elem.text:
                doi = doi_elem.text

            # Extract categories
            categories = []
            for cat_elem in entry.findall("atom:category", ns):
                term = cat_elem.get("term")
                if term:
                    categories.append(term)

            # Extract PDF link
            pdf_url = None
            for link_elem in entry.findall("atom:link", ns):
                if link_elem.get("title") == "pdf":
                    pdf_url = link_elem.get("href")

            return RawPaper(
                source=self.connector_name,
                source_id=arxiv_id,
                title=title,
                authors=authors,
                year=year,
                doi=doi,
                abstract=abstract,
                venue="arXiv",
                url=arxiv_url,
                citation_count=None,  # arXiv doesn't provide citation counts
                paper_type="research",
                raw_metadata={
                    "categories": categories,
                    "pdf_url": pdf_url,
                },
            )

        except Exception as e:
            logger.error("arxiv_parse_entry_failed", error=str(e))
            return None

    async def health_check(self) -> bool:
        """Check if arXiv API is accessible."""
        try:
            params = {
                "search_query": "ti:test",
                "max_results": 1,
            }
            response = await self.client.get(self.BASE_URL, params=params)
            return response.status_code == 200
        except Exception:
            return False
