"""Tests for connector manager caching and parallel search."""

from unittest.mock import AsyncMock

import httpx
import pytest

from app.connectors.base import RawPaper, SearchQuery, SearchResult
from app.connectors.manager import ConnectorManager
from app.services.cache_service import CacheService


class StubConnector:
    def __init__(self, name: str):
        self._name = name
        self.search_calls = 0

    @property
    def connector_name(self):
        return self._name

    @property
    def base_url(self):
        return f"https://{self._name}.example.com"

    async def search(self, query):
        self.search_calls += 1
        return SearchResult(
            source=self._name,
            query=query,
            papers=[
                RawPaper(
                    source=self._name,
                    source_id=f"{self._name}-1",
                    title=f"{self._name} Paper",
                    authors=["A"],
                    year=2024,
                    doi=f"10.1234/{self._name}",
                )
            ],
            total_results=1,
        )

    async def get_paper(self, identifier):
        return None

    async def get_citations(self, paper_id, limit=20):
        return []

    async def get_references(self, paper_id, limit=20):
        return []

    async def health_check(self):
        return True


@pytest.mark.asyncio
async def test_search_and_merge_uses_cache_on_second_call():
    store: dict[str, str] = {}

    async def mock_get(key):
        return store.get(key)

    async def mock_setex(key, ttl, value):
        store[key] = value

    redis = AsyncMock()
    redis.get = mock_get
    redis.setex = mock_setex
    cache = CacheService(redis, default_ttl_seconds=60, prefix="literature")

    manager = ConnectorManager(cache_service=cache, cache_ttl_seconds=60)
    connector = StubConnector("openalex")
    manager.register_connector("openalex", connector)

    query = SearchQuery(text="transformers", limit=5)
    first = await manager.search_and_merge(query)
    second = await manager.search_and_merge(query)

    assert len(first) == 1
    assert len(second) == 1
    assert connector.search_calls == 1
    assert len(store) >= 1


@pytest.mark.asyncio
async def test_search_all_retries_failed_connector_once():
    class FlakyConnector(StubConnector):
        def __init__(self):
            super().__init__("flaky")
            self.attempts = 0

        async def search(self, query):
            self.attempts += 1
            if self.attempts == 1:
                raise httpx.TimeoutException("temporary outage")
            return await super().search(query)

    manager = ConnectorManager()
    flaky = FlakyConnector()
    manager.register_connector("flaky", flaky)

    results = await manager.search_all(SearchQuery(text="retry test", limit=3))
    assert "flaky" in results
    assert flaky.attempts == 2