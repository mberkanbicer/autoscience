"""Tests for LLM providers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.llm.base import Message, LLMProvider, CompletionResult
from app.llm.router import LLMRouter, create_default_router


class MockProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, name: str = "mock", should_fail: bool = False):
        self._name = name
        self._should_fail = should_fail

    @property
    def provider_name(self) -> str:
        return self._name

    async def complete(self, messages, model=None, temperature=0.7, max_tokens=None, **kwargs):
        if self._should_fail:
            raise RuntimeError(f"Mock provider {self._name} failed")
        return CompletionResult(
            content="Mock response",
            model=model or "mock-model",
            provider=self._name,
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            cost_usd=0.001,
        )

    async def complete_structured(self, messages, schema, model=None, temperature=0.3, **kwargs):
        if self._should_fail:
            raise RuntimeError(f"Mock provider {self._name} failed")
        completion = await self.complete(messages, model=model)
        return StructuredOutput(
            data={"result": "mock_data"},
            completion=completion,
        )

    def count_tokens(self, text):
        return len(text) // 4


def test_message_creation():
    """Test Message dataclass creation."""
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"


def test_completion_result():
    """Test CompletionResult dataclass creation."""
    result = CompletionResult(
        content="Test",
        model="test-model",
        provider="test",
        usage={"total_tokens": 100},
        cost_usd=0.01,
    )
    assert result.content == "Test"
    assert result.model == "test-model"
    assert result.usage["total_tokens"] == 100


def test_router_registration():
    """Test provider registration in router."""
    router = LLMRouter()
    provider = MockProvider("test")
    router.register_provider("test", provider)

    assert "test" in router.providers
    assert router.get_provider("test") == provider


def test_router_default():
    """Test default provider setting."""
    router = LLMRouter()
    provider = MockProvider("test")
    router.register_provider("test", provider)
    router.set_default("test")

    assert router.get_provider() == provider


def test_router_default_not_found():
    """Test error when provider not found."""
    router = LLMRouter()
    with pytest.raises(ValueError):
        router.get_provider("nonexistent")


@pytest.mark.asyncio
async def test_router_complete_success():
    """Test successful completion through router."""
    router = LLMRouter()
    provider = MockProvider("test")
    router.register_provider("test", provider)
    router.set_default("test")

    messages = [Message(role="user", content="Hello")]
    result = await router.complete(messages)

    assert result.content == "Mock response"
    assert result.provider == "test"


@pytest.mark.asyncio
async def test_router_complete_with_fallback():
    """Test fallback when primary provider fails."""
    router = LLMRouter()

    failing_provider = MockProvider("failing", should_fail=True)
    working_provider = MockProvider("working")

    router.register_provider("failing", failing_provider)
    router.register_provider("working", working_provider)
    router.set_default("failing")
    router.set_fallback_chain(["working"])

    messages = [Message(role="user", content="Hello")]
    result = await router.complete(messages)

    assert result.content == "Mock response"
    assert result.provider == "working"


@pytest.mark.asyncio
async def test_router_complete_all_fail():
    """Test error when all providers fail."""
    router = LLMRouter()

    failing1 = MockProvider("failing1", should_fail=True)
    failing2 = MockProvider("failing2", should_fail=True)

    router.register_provider("failing1", failing1)
    router.register_provider("failing2", failing2)
    router.set_default("failing1")
    router.set_fallback_chain(["failing2"])

    messages = [Message(role="user", content="Hello")]

    with pytest.raises(RuntimeError):
        await router.complete(messages)


def test_router_health_check():
    """Test health check returns status for all providers."""
    router = LLMRouter()
    provider1 = MockProvider("p1")
    provider2 = MockProvider("p2")

    router.register_provider("p1", provider1)
    router.register_provider("p2", provider2)

    # Sync test - health_check is async but MockProvider is always healthy
    import asyncio

    results = asyncio.run(router.health_check())

    assert results["p1"] is True
    assert results["p2"] is True


def test_create_default_router():
    """Test creating a router with providers."""
    router = create_default_router(
        openai_api_key="test-key",
        anthropic_api_key="test-key",
        default_provider="openai",
    )

    assert "openai" in router.providers
    assert "anthropic" in router.providers
    assert router.default_provider == "openai"
