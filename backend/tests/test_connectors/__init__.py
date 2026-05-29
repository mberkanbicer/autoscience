"""Tests for academic source connectors."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.connectors.base import RawPaper, SearchQuery, SearchResult
from app.connectors.manager import ConnectorManager, create_default_manager


class MockConnector:
    """Mock academic connector for testing."""

    def __init__(self, name: str = "mock", should_fail: bool = False):
        self._name = name
        self._should_fail = should_fail

    @property
    def connector_name(self):
        return self._name

    @property
    def base_url(self):
        return f"https://{self._name}.example.com"

    async def search(self, query):
        if self._should_fail:
            raise RuntimeError(f"Mock connector {self._name} failed")
        return SearchResult(
            source=self._name,
            query=query,
            papers=[
                RawPaper(
                    source=self._name,
                    source_id="1",
                    title="Test Paper",
                    authors=["Author 1"],
                    year=2024,
                    doi="10.1234/test",
                )
            ],
            total_results=1,
        )

    async def get_paper(self, identifier):
        if self._should_fail:
            raise RuntimeError(f"Mock connector {self._name} failed")
        return RawPaper(
            source=self._name,
            source_id=identifier,
            title="Test Paper",
            authors=["Author 1"],
            year=2024,
        )

    async def get_citations(self, paper_id, limit=20):
        return []

    async def get_references(self, paper_id, limit=20):
        return []

    async def health_check(self):
        return not self._should_fail


def test_raw_paper_creation():
    """Test RawPaper dataclass creation."""
    paper = RawPaper(
        source="test",
        source_id="123",
        title="Test Paper",
        authors=["Author 1", "Author 2"],
        year=2024,
        doi="10.1234/test",
        abstract="Test abstract",
    )
    assert paper.source == "test"
    assert paper.title == "Test Paper"
    assert len(paper.authors) == 2


def test_search_query_creation():
    """Test SearchQuery dataclass creation."""
    query = SearchQuery(
        text="machine learning",
        year_from=2020,
        year_to=2024,
        limit=50,
        sort_by="citations",
    )
    assert query.text == "machine learning"
    assert query.year_from == 2020
    assert query.limit == 50


def test_search_result_creation():
    """Test SearchResult dataclass creation."""
    result = SearchResult(
        source="test",
        query=SearchQuery(text="test"),
        papers=[],
        total_results=0,
    )
    assert result.source == "test"
    assert result.total_results == 0


def test_manager_registration():
    """Test connector registration in manager."""
    manager = ConnectorManager()
    connector = MockConnector("test")
    manager.register_connector("test", connector)

    assert "test" in manager.connectors
    assert manager.get_connector("test") == connector


def test_manager_get_connector_not_found():
    """Test error when connector not found."""
    manager = ConnectorManager()
    with pytest.raises(ValueError):
        manager.get_connector("nonexistent")


@pytest.mark.asyncio
async def test_manager_search_all():
    """Test searching across multiple connectors."""
    manager = ConnectorManager()
    connector1 = MockConnector("source1")
    connector2 = MockConnector("source2")

    manager.register_connector("source1", connector1)
    manager.register_connector("source2", connector2)

    query = SearchQuery(text="test")
    results = await manager.search_all(query)

    assert "source1" in results
    assert "source2" in results
    assert len(results["source1"].papers) == 1


@pytest.mark.asyncio
async def test_manager_search_with_failure():
    """Test search with one connector failing."""
    manager = ConnectorManager()
    connector1 = MockConnector("source1")
    connector2 = MockConnector("source2", should_fail=True)

    manager.register_connector("source1", connector1)
    manager.register_connector("source2", connector2)

    query = SearchQuery(text="test")
    results = await manager.search_all(query)

    assert "source1" in results
    assert "source2" not in results  # Failed connector not in results


@pytest.mark.asyncio
async def test_manager_search_and_merge():
    """Test merging results from multiple sources."""
    manager = ConnectorManager()
    connector1 = MockConnector("source1")
    connector2 = MockConnector("source2")

    manager.register_connector("source1", connector1)
    manager.register_connector("source2", connector2)

    query = SearchQuery(text="test")
    papers = await manager.search_and_merge(query)

    # Should have papers from both sources
    assert len(papers) >= 1


@pytest.mark.asyncio
async def test_manager_get_paper():
    """Test getting paper from multiple sources."""
    manager = ConnectorManager()
    connector1 = MockConnector("source1")
    connector2 = MockConnector("source2")

    manager.register_connector("source1", connector1)
    manager.register_connector("source2", connector2)

    paper = await manager.get_paper("10.1234/test")
    assert paper is not None
    assert paper.title == "Test Paper"


@pytest.mark.asyncio
async def test_manager_health_check():
    """Test health check for all connectors."""
    manager = ConnectorManager()
    connector1 = MockConnector("source1")
    connector2 = MockConnector("source2", should_fail=True)

    manager.register_connector("source1", connector1)
    manager.register_connector("source2", connector2)

    results = await manager.health_check()

    assert results["source1"] is True
    assert results["source2"] is False


def test_create_default_manager():
    """Test creating a default manager."""
    manager = create_default_manager(
        openalex_email="test@example.com",
        semantic_scholar_api_key="test-key",
    )

    assert "openalex" in manager.connectors
    assert "semantic_scholar" in manager.connectors
    assert "crossref" in manager.connectors
    assert "arxiv" in manager.connectors
    assert "pubmed" in manager.connectors
