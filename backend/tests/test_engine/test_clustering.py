"""Tests for the clustering engine."""

import pytest
from unittest.mock import Mock, AsyncMock

from app.engine.clustering import ClusteringEngine
from app.llm.router import LLMRouter


@pytest.fixture
def mock_llm():
    router = Mock(spec=LLMRouter)
    router.has_provider = Mock(return_value=False)
    return router


@pytest.fixture
def engine(mock_llm):
    return ClusteringEngine(mock_llm)


def test_simple_clustering(engine):
    papers = [
        {"title": "Deep Learning for NLP", "id": "1"},
        {"title": "Deep Learning in Vision", "id": "2"},
        {"title": "Deep Learning for Graphs", "id": "3"},
    ]
    result = engine._simple_cluster(papers)
    assert result is not None
    assert hasattr(result, "clusters")


@pytest.mark.asyncio
async def test_cluster_with_no_provider(engine):
    papers = [
        {"title": "Paper A about machine learning", "id": "1"},
        {"title": "Paper B about machine learning", "id": "2"},
    ]
    result = await engine.cluster_papers(papers)
    assert result is not None
    assert hasattr(result, "clusters")
    assert len(result.clusters) >= 1


@pytest.mark.asyncio
async def test_cluster_empty_papers(engine):
    result = await engine.cluster_papers([])
    assert result is None or (hasattr(result, "clusters") and len(result.clusters) == 0)


@pytest.mark.asyncio
async def test_cluster_single_paper(engine):
    result = await engine.cluster_papers([{"title": "Single paper", "id": "1"}])
    assert result is not None
    assert hasattr(result, "clusters")
