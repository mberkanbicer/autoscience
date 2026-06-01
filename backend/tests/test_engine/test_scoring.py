"""Tests for the scoring engine."""

import pytest
from unittest.mock import Mock, AsyncMock

from app.engine.scoring import IdeaScoringEngine, IdeaScore
from app.llm.router import LLMRouter


@pytest.fixture
def mock_llm():
    router = Mock(spec=LLMRouter)
    router.has_provider = Mock(return_value=False)
    return router


@pytest.fixture
def engine(mock_llm):
    return IdeaScoringEngine(mock_llm)


@pytest.mark.asyncio
async def test_simple_score(engine):
    result = await engine.score_idea(
        idea={"id": "test", "current_text": "Test research idea"},
        papers=[{"title": "Related work", "year": 2023}],
        conflicts=[{"type": "methodological", "description": "Test conflict"}],
    )
    assert result is not None
    assert hasattr(result, "overall_value") or hasattr(result, "dimensions")


def test_blueprint_scoring(engine):
    score = engine._simple_score(
        idea_id="test",
        idea_text="Test idea",
        papers=[{"title": "Related"}],
        conflicts=[{"type": "methodological"}],
    )
    assert hasattr(score, "novelty")
    assert hasattr(score, "overall_value")
    overall = engine._calculate_overall_value(score)
    assert 0 <= overall <= 10
    assert isinstance(overall, float)


@pytest.mark.asyncio
async def test_score_empty_idea(engine):
    result = await engine.score_idea(
        idea={"id": "", "current_text": ""},
    )
    assert result is not None
