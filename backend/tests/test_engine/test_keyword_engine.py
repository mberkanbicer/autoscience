"""Tests for the keyword expansion engine."""

import pytest
from unittest.mock import Mock, AsyncMock

from app.engine.keyword_engine import KeywordExpansionEngine, KeywordExpansion
from app.llm.base import CompletionResult, StructuredOutput


class MockRouter:
    has_provider = Mock(return_value=True)
    complete_structured = AsyncMock(return_value=StructuredOutput(
        data={"core_concepts": ["transformer", "attention"], "synonyms": ["seq2seq", "self-attention"], "method_terms": ["fine-tuning", "pretraining"]},
        completion=CompletionResult(content="{}", model="test", provider="test"),
    ))


class MockRouterNoProvider:
    has_provider = Mock(return_value=False)


@pytest.fixture
def engine():
    return KeywordExpansionEngine(MockRouter())


@pytest.fixture
def engine_no_provider():
    return KeywordExpansionEngine(MockRouterNoProvider())


@pytest.mark.asyncio
async def test_expand_keywords_with_llm(engine):
    result = await engine.expand_keywords("test research idea")
    assert isinstance(result, KeywordExpansion)
    assert len(result.core_concepts) > 0
    assert len(result.synonyms) > 0


@pytest.mark.asyncio
async def test_expand_keywords_no_provider(engine_no_provider):
    result = await engine_no_provider.expand_keywords("test idea")
    assert isinstance(result, KeywordExpansion)
    assert len(result.core_concepts) > 0  # fallback works


@pytest.mark.asyncio
async def test_expand_keywords_empty_idea(engine):
    result = await engine.expand_keywords("")
    assert isinstance(result, KeywordExpansion)


@pytest.mark.asyncio
async def test_expand_keywords_json_parse_fallback(engine_no_provider):
    """Without provider, fallback to simple expansion."""
    import asyncio
    result = await engine_no_provider.expand_keywords("machine learning transformers")
    assert isinstance(result, KeywordExpansion)
    assert "machine" in result.core_concepts or "learning" in result.core_concepts
