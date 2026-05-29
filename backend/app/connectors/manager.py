"""Academic source connector manager."""

import structlog
from typing import Any

from .base import AcademicConnector, SearchQuery, SearchResult, RawPaper
from .openalex import OpenAlexConnector
from .semantic_scholar import SemanticScholarConnector
from .crossref import CrossrefConnector
from .arxiv import ArxivConnector
from .pubmed import PubMedConnector

logger = structlog.get_logger()


class ConnectorManager:
    """Manager for multiple academic source connectors."""

    def __init__(self):
        self.connectors: dict[str, AcademicConnector] = {}

    def register_connector(self, name: str, connector: AcademicConnector) -> None:
        """Register a connector."""
        self.connectors[name] = connector
        logger.info("connector_registered", connector=name)

    def get_connector(self, name: str) -> AcademicConnector:
        """Get a connector by name."""
        if name not in self.connectors:
            raise ValueError(f"Connector {name} not registered")
        return self.connectors[name]

    async def search_all(
        self,
        query: SearchQuery,
        sources: list[str] | None = None,
    ) -> dict[str, SearchResult]:
        """Search across multiple sources."""
        results = {}
        sources_to_search = sources or list(self.connectors.keys())

        for source_name in sources_to_search:
            if source_name not in self.connectors:
                logger.warning("connector_not_found", source=source_name)
                continue

            try:
                connector = self.connectors[source_name]
                result = await connector.search(query)
                results[source_name] = result
            except Exception as e:
                logger.error("search_failed", source=source_name, error=str(e))

        return results

    async def search_and_merge(
        self,
        query: SearchQuery,
        sources: list[str] | None = None,
    ) -> list[RawPaper]:
        """Search and merge results from multiple sources."""
        results = await self.search_all(query, sources)

        # Merge and deduplicate
        all_papers = []
        seen_dois = set()
        seen_titles = set()

        for source_name, result in results.items():
            for paper in result.papers:
                # Deduplicate by DOI
                if paper.doi and paper.doi in seen_dois:
                    continue

                # Deduplicate by title (normalized)
                normalized_title = paper.title.lower().strip()
                if normalized_title in seen_titles:
                    continue

                if paper.doi:
                    seen_dois.add(paper.doi)
                seen_titles.add(normalized_title)
                all_papers.append(paper)

        # Sort by citation count (descending)
        all_papers.sort(
            key=lambda p: p.citation_count or 0,
            reverse=True,
        )

        return all_papers

    async def get_paper(
        self,
        identifier: str,
        sources: list[str] | None = None,
    ) -> RawPaper | None:
        """Get a paper from multiple sources."""
        sources_to_search = sources or list(self.connectors.keys())

        for source_name in sources_to_search:
            if source_name not in self.connectors:
                continue

            try:
                connector = self.connectors[source_name]
                paper = await connector.get_paper(identifier)
                if paper:
                    return paper
            except Exception as e:
                logger.error("get_paper_failed", source=source_name, error=str(e))

        return None

    async def health_check(self) -> dict[str, bool]:
        """Check health of all connectors."""
        results = {}
        for name, connector in self.connectors.items():
            try:
                results[name] = await connector.health_check()
            except Exception:
                results[name] = False
        return results


def create_default_manager(
    openalex_email: str | None = None,
    semantic_scholar_api_key: str | None = None,
    pubmed_api_key: str | None = None,
) -> ConnectorManager:
    """Create a connector manager with default connectors."""
    manager = ConnectorManager()

    # Always register free connectors
    manager.register_connector("openalex", OpenAlexConnector(email=openalex_email))
    manager.register_connector("semantic_scholar", SemanticScholarConnector(api_key=semantic_scholar_api_key))
    manager.register_connector("crossref", CrossrefConnector(email=openalex_email))
    manager.register_connector("arxiv", ArxivConnector())
    manager.register_connector("pubmed", PubMedConnector(api_key=pubmed_api_key))

    return manager
