"""PubMed academic source connector."""

import httpx
import structlog
from typing import Any
import xml.etree.ElementTree as ET

from .base import AcademicConnector, RawPaper, SearchQuery, SearchResult

logger = structlog.get_logger()


class PubMedConnector(AcademicConnector):
    """Connector for PubMed/NCBI E-utilities API (free, no API key required)."""

    SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    def __init__(self, api_key: str | None = None):
        """
        Initialize PubMed connector.

        Args:
            api_key: Optional NCBI API key for higher rate limits.
        """
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    @property
    def connector_name(self) -> str:
        return "pubmed"

    @property
    def base_url(self) -> str:
        return "https://pubmed.ncbi.nlm.nih.gov"

    async def search(self, query: SearchQuery) -> SearchResult:
        """Search for papers using PubMed E-utilities."""
        # Build search query
        search_query = self._build_search_query(query)

        params: dict[str, Any] = {
            "db": "pubmed",
            "term": search_query,
            "retmax": query.limit,
            "retmode": "json",
            "sort": self._get_sort_param(query.sort_by),
        }

        if self.api_key:
            params["api_key"] = self.api_key

        try:
            # First, get PMIDs
            response = await self.client.get(self.SEARCH_URL, params=params)
            response.raise_for_status()
            data = response.json()

            pmids = data.get("esearchresult", {}).get("idlist", [])
            total = int(data.get("esearchresult", {}).get("count", 0))

            if not pmids:
                return SearchResult(
                    source=self.connector_name,
                    query=query,
                    papers=[],
                    total_results=total,
                    has_more=False,
                )

            # Fetch paper details
            papers = await self._fetch_papers(pmids)

            return SearchResult(
                source=self.connector_name,
                query=query,
                papers=papers,
                total_results=total,
                has_more=len(papers) < total,
            )

        except Exception as e:
            logger.error("pubmed_search_failed", error=str(e), query=query.text)
            raise

    async def get_paper(self, identifier: str) -> RawPaper | None:
        """Get a paper by PMID or DOI."""
        # Check if it's a DOI
        if identifier.startswith("10."):
            # Search by DOI
            params = {
                "db": "pubmed",
                "term": f"{identifier}[doi]",
                "retmax": 1,
                "retmode": "json",
            }
            if self.api_key:
                params["api_key"] = self.api_key

            response = await self.client.get(self.SEARCH_URL, params=params)
            response.raise_for_status()
            data = response.json()

            pmids = data.get("esearchresult", {}).get("idlist", [])
            if not pmids:
                return None

            identifier = pmids[0]

        # Fetch by PMID
        papers = await self._fetch_papers([identifier])
        return papers[0] if papers else None

    async def get_citations(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers that cite this paper."""
        # PubMed doesn't have a direct citations API
        # We can search for papers that reference this PMID
        search_query = f"{paper_id}[uid] AND ({paper_id}[uid - from] in citations)"
        params = {
            "db": "pubmed",
            "term": search_query,
            "retmax": limit,
            "retmode": "json",
        }

        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = await self.client.get(self.SEARCH_URL, params=params)
            response.raise_for_status()
            data = response.json()

            pmids = data.get("esearchresult", {}).get("idlist", [])
            return await self._fetch_papers(pmids[:limit])

        except Exception as e:
            logger.error("pubmed_citations_failed", error=str(e), paper_id=paper_id)
            return []

    async def get_references(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        """Get papers referenced by this paper."""
        # Similar to citations, PubMed doesn't have a direct references API
        return []

    async def _fetch_papers(self, pmids: list[str]) -> list[RawPaper]:
        """Fetch paper details for a list of PMIDs."""
        if not pmids:
            return []

        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        }

        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = await self.client.get(self.FETCH_URL, params=params)
            response.raise_for_status()

            return self._parse_xml_response(response.text)

        except Exception as e:
            logger.error("pubmed_fetch_failed", error=str(e))
            return []

    def _build_search_query(self, query: SearchQuery) -> str:
        """Build PubMed search query string."""
        parts = [query.text]

        # Add date filters
        if query.year_from:
            parts.append(f"{query.year_from}:{query.year_to or '3000'}[dp]")

        return " AND ".join(parts)

    def _get_sort_param(self, sort_by: str) -> str:
        """Convert sort_by to PubMed API parameter."""
        sort_map = {
            "relevance": "relevance",
            "citations": "relevance",  # PubMed doesn't have citation count sorting
            "date": "pub_date",
        }
        return sort_map.get(sort_by, "relevance")

    def _parse_xml_response(self, xml_content: str) -> list[RawPaper]:
        """Parse PubMed XML response."""
        papers = []

        try:
            root = ET.fromstring(xml_content)

            for article in root.findall(".//PubmedArticle"):
                paper = self._parse_article(article)
                if paper:
                    papers.append(paper)

        except Exception as e:
            logger.error("pubmed_parse_failed", error=str(e))

        return papers

    def _parse_article(self, article: ET.Element) -> RawPaper | None:
        """Parse a PubmedArticle element."""
        try:
            # Get PMID
            pmid_elem = article.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else ""
            if not pmid:
                return None

            # Get MedlineCitation
            citation = article.find(".//MedlineCitation")
            if citation is None:
                return None

            # Get Article
            medline_article = citation.find("Article")
            if medline_article is None:
                return None

            # Get title
            title_elem = medline_article.find("ArticleTitle")
            title = title_elem.text if title_elem is not None and title_elem.text else ""
            if not title:
                return None

            # Get authors
            authors = []
            author_list = medline_article.find("AuthorList")
            if author_list is not None:
                for author_elem in author_list.findall("Author"):
                    last_name = author_elem.findtext("LastName", "")
                    first_name = author_elem.findtext("ForeName", "")
                    name = f"{first_name} {last_name}".strip()
                    if name:
                        authors.append(name)

            # Get year
            year = None
            journal = medline_article.find("Journal")
            if journal is not None:
                pub_date = journal.find("JournalIssue/PubDate")
                if pub_date is not None:
                    year_elem = pub_date.find("Year")
                    if year_elem is not None and year_elem.text:
                        year = int(year_elem.text)

            # Get abstract
            abstract = None
            abstract_elem = medline_article.find("Abstract")
            if abstract_elem is not None:
                abstract_parts = []
                for text_elem in abstract_elem.findall("AbstractText"):
                    if text_elem.text:
                        abstract_parts.append(text_elem.text)
                abstract = " ".join(abstract_parts) if abstract_parts else None

            # Get journal
            venue = None
            if journal is not None:
                title_elem = journal.find("Title")
                if title_elem is not None:
                    venue = title_elem.text

            # Get DOI
            doi = None
            article_ids = article.find(".//ArticleIdList")
            if article_ids is not None:
                for id_elem in article_ids.findall("ArticleId"):
                    if id_elem.get("IdType") == "doi":
                        doi = id_elem.text
                        break

            # Get PMC ID
            pmc_id = None
            if article_ids is not None:
                for id_elem in article_ids.findall("ArticleId"):
                    if id_elem.get("IdType") == "pmc":
                        pmc_id = id_elem.text
                        break

            return RawPaper(
                source=self.connector_name,
                source_id=pmid,
                title=title,
                authors=authors,
                year=year,
                doi=doi,
                abstract=abstract,
                venue=venue,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                citation_count=None,
                paper_type="research",
                raw_metadata={"pmid": pmid, "pmc_id": pmc_id},
            )

        except Exception as e:
            logger.error("pubmed_parse_article_failed", error=str(e))
            return None

    async def health_check(self) -> bool:
        """Check if PubMed API is accessible."""
        try:
            params = {
                "db": "pubmed",
                "term": "test",
                "retmax": 1,
                "retmode": "json",
            }
            response = await self.client.get(self.SEARCH_URL, params=params)
            return response.status_code == 200
        except Exception:
            return False
