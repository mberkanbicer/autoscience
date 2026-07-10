"""Unit tests for the HealthService.

Tests each check method (database, redis, llm, connectors) with mocked
dependencies as well as the aggregated ``check_all()`` response.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.health_service import HealthResult, OverallHealth, HealthService


# ── Helpers ──────────────────────────────────────────────────────────────


class FakeAsyncSession:
    """Minimal stand-in for an async DB session that records ``execute()``
    calls and raises when told to."""

    def __init__(self, execute_should_fail: bool = False):
        self._fail = execute_should_fail
        self.executed: list[Any] = []

    async def __aenter__(self) -> "FakeAsyncSession":
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass

    async def execute(self, stmt: Any) -> None:
        self.executed.append(stmt)
        if self._fail:
            raise RuntimeError("DB connection refused")


class FakeAsyncSessionFactory:
    """Returns a shared ``FakeAsyncSession`` instance on every call.

    Mimics ``async_sessionmaker`` — ``__call__`` is synchronous and returns
    an async context manager directly (not a coroutine).
    """

    def __init__(self, session: FakeAsyncSession):
        self._session = session

    def __call__(self) -> FakeAsyncSession:
        return self._session


@dataclass
class FakeConnectorManager:
    """Minimal mock for ``ConnectorManager.health_check()``."""

    results: dict[str, bool] = field(default_factory=dict)

    async def health_check(self) -> dict[str, bool]:
        return self.results


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def healthy_db() -> FakeAsyncSessionFactory:
    return FakeAsyncSessionFactory(FakeAsyncSession())


@pytest.fixture
def unhealthy_db() -> FakeAsyncSessionFactory:
    return FakeAsyncSessionFactory(FakeAsyncSession(execute_should_fail=True))


@pytest.fixture
def healthy_connectors() -> FakeConnectorManager:
    return FakeConnectorManager(
        results={"openalex": True, "semantic_scholar": True, "arxiv": True}
    )


@pytest.fixture
def degraded_connectors() -> FakeConnectorManager:
    return FakeConnectorManager(
        results={"openalex": True, "semantic_scholar": False, "arxiv": True}
    )


@pytest.fixture
def empty_db() -> HealthService:
    return HealthService(db_session_factory=None, redis_url="", connector_manager=None)


# ── Individual check tests ───────────────────────────────────────────────


class TestCheckDatabase:
    async def test_healthy(self, healthy_db: FakeAsyncSessionFactory) -> None:
        service = HealthService(db_session_factory=healthy_db)
        result = await service.check_database()
        assert result.status == "healthy"
        assert result.error is None

    async def test_unhealthy(self, unhealthy_db: FakeAsyncSessionFactory) -> None:
        service = HealthService(db_session_factory=unhealthy_db)
        result = await service.check_database()
        assert result.status == "unhealthy"
        assert "DB connection refused" in (result.error or "")

    async def test_not_configured(self) -> None:
        service = HealthService(db_session_factory=None)
        result = await service.check_database()
        assert result.status == "not_configured"

    async def test_executes_select_one(self, healthy_db: FakeAsyncSessionFactory) -> None:
        service = HealthService(db_session_factory=healthy_db)
        await service.check_database()
        session = healthy_db()
        assert len(session.executed) >= 1


class TestCheckRedis:
    async def test_not_configured(self) -> None:
        service = HealthService(redis_url="")
        result = await service.check_redis()
        assert result.status == "not_configured"

    async def test_healthy(self) -> None:
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.info = AsyncMock(return_value={"redis_version": "7.2.0"})

        with patch("redis.asyncio.Redis.from_url", return_value=mock_redis):
            service = HealthService(redis_url="redis://localhost:6379/0")
            result = await service.check_redis()

        assert result.status == "healthy"
        assert result.details.get("redis_version") == "7.2.0"

    async def test_connection_failure(self) -> None:
        with patch(
            "redis.asyncio.Redis.from_url",
            side_effect=ConnectionError("Connection refused"),
        ):
            service = HealthService(redis_url="redis://localhost:6379/0")
            result = await service.check_redis()

        assert result.status == "unhealthy"
        assert "Connection refused" in (result.error or "")

    async def test_ping_failure(self) -> None:
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=RuntimeError("PONG timeout"))

        with patch("redis.asyncio.Redis.from_url", return_value=mock_redis):
            service = HealthService(redis_url="redis://localhost:6379/0")
            result = await service.check_redis()

        assert result.status == "unhealthy"
        assert "PONG timeout" in (result.error or "")


class TestCheckLlm:
    async def test_healthy_with_openai(self) -> None:
        settings = MagicMock()
        settings.openai_api_key = "sk-..."
        settings.anthropic_api_key = ""
        settings.openrouter_api_key = ""
        settings.local_llm_base_url = ""
        settings.llamacpp_base_url = ""
        settings.default_llm_provider = "openai"

        with patch("app.config.get_settings", return_value=settings):
            service = HealthService()
            result = await service.check_llm()

        assert result.status == "healthy"
        assert result.details.get("configured_count") == 1
        assert result.details["providers"]["openai"]["configured"] is True
        assert result.details["providers"]["anthropic"]["configured"] is False

    async def test_degraded_when_no_providers(self) -> None:
        settings = MagicMock()
        settings.openai_api_key = ""
        settings.anthropic_api_key = ""
        settings.openrouter_api_key = ""
        settings.local_llm_base_url = ""
        settings.llamacpp_base_url = ""
        settings.default_llm_provider = "openai"

        with patch("app.config.get_settings", return_value=settings):
            service = HealthService()
            result = await service.check_llm()

        assert result.status == "degraded"
        assert result.details.get("configured_count") == 0

    async def test_reports_multiple_providers(self) -> None:
        settings = MagicMock()
        settings.openai_api_key = "sk-..."
        settings.anthropic_api_key = "sk-ant-..."
        settings.openrouter_api_key = ""
        settings.local_llm_base_url = "http://localhost:11434"
        settings.llamacpp_base_url = ""
        settings.default_llm_provider = "anthropic"

        with patch("app.config.get_settings", return_value=settings):
            service = HealthService()
            result = await service.check_llm()

        assert result.status == "healthy"
        assert result.details.get("configured_count") == 3
        assert result.details["default"] == "anthropic"


class TestCheckConnectors:
    async def test_not_available(self) -> None:
        service = HealthService()
        result = await service.check_connectors()
        assert result.status == "not_available"

    async def test_healthy(self, healthy_connectors: FakeConnectorManager) -> None:
        service = HealthService(connector_manager=healthy_connectors)
        result = await service.check_connectors()
        assert result.status == "healthy"
        assert result.details.get("healthy") == 3
        assert result.details.get("total") == 3

    async def test_degraded(self, degraded_connectors: FakeConnectorManager) -> None:
        service = HealthService(connector_manager=degraded_connectors)
        result = await service.check_connectors()
        assert result.status == "degraded"
        assert result.details.get("healthy") == 2
        assert result.details.get("total") == 3

    async def test_propagates_exception(self) -> None:
        class BrokenManager:
            async def health_check(self) -> dict[str, bool]:
                msg = "Manager unavailable"
                raise RuntimeError(msg)

        service = HealthService(connector_manager=BrokenManager())
        result = await service.check_connectors()
        assert result.status == "unhealthy"


# ── Aggregated check_all tests ───────────────────────────────────────────


class TestCheckAll:
    async def test_all_healthy(
        self, healthy_db: FakeAsyncSessionFactory, healthy_connectors: FakeConnectorManager
    ) -> None:
        settings = MagicMock()
        settings.openai_api_key = "sk-..."
        settings.anthropic_api_key = ""
        settings.openrouter_api_key = ""
        settings.local_llm_base_url = ""
        settings.llamacpp_base_url = ""
        settings.default_llm_provider = "openai"

        with patch("app.config.get_settings", return_value=settings):
            with patch("redis.asyncio.Redis.from_url") as mock_redis_factory:
                mock_redis = AsyncMock()
                mock_redis.ping = AsyncMock(return_value=True)
                mock_redis.info = AsyncMock(return_value={"redis_version": "7.2.0"})
                mock_redis_factory.return_value = mock_redis

                service = HealthService(
                    db_session_factory=healthy_db,
                    redis_url="redis://localhost:6379/0",
                    connector_manager=healthy_connectors,
                )
                overall = await service.check_all()

        assert overall.status == "healthy"
        assert overall.checks["database"].status == "healthy"
        assert overall.checks["redis"].status == "healthy"
        assert overall.checks["llm"].status == "healthy"
        assert overall.checks["connectors"].status == "healthy"

    async def test_database_unhealthy(
        self, unhealthy_db: FakeAsyncSessionFactory, healthy_connectors: FakeConnectorManager
    ) -> None:
        settings = MagicMock()
        settings.openai_api_key = "sk-..."
        settings.anthropic_api_key = ""
        settings.openrouter_api_key = ""
        settings.local_llm_base_url = ""
        settings.llamacpp_base_url = ""
        settings.default_llm_provider = "openai"

        with patch("app.config.get_settings", return_value=settings):
            with patch("redis.asyncio.Redis.from_url") as mock_redis_factory:
                mock_redis = AsyncMock()
                mock_redis.ping = AsyncMock(return_value=True)
                mock_redis.info = AsyncMock(return_value={"redis_version": "7.2.0"})
                mock_redis_factory.return_value = mock_redis

                service = HealthService(
                    db_session_factory=unhealthy_db,
                    redis_url="redis://localhost:6379/0",
                    connector_manager=healthy_connectors,
                )
                overall = await service.check_all()

        assert overall.status == "unhealthy"
        assert overall.checks["database"].status == "unhealthy"

    async def test_only_db_configured(self, healthy_db: FakeAsyncSessionFactory) -> None:
        settings = MagicMock()
        settings.openai_api_key = ""
        settings.anthropic_api_key = ""
        settings.openrouter_api_key = ""
        settings.local_llm_base_url = ""
        settings.llamacpp_base_url = ""
        settings.default_llm_provider = "openai"

        with patch("app.config.get_settings", return_value=settings):
            service = HealthService(
                db_session_factory=healthy_db,
                redis_url="",
                connector_manager=None,
            )
            overall = await service.check_all()

        # DB healthy, Redis not_configured, LLM degraded, connectors not_available
        # → "degraded" (no unhealthy component)
        assert overall.status == "degraded"
        assert overall.checks["database"].status == "healthy"
        assert overall.checks["redis"].status == "not_configured"
        assert overall.checks["llm"].status == "degraded"
        assert overall.checks["connectors"].status == "not_available"

    async def test_mixed_healthy_and_not_configured(
        self, healthy_db: FakeAsyncSessionFactory
    ) -> None:
        """DB healthy + Redis not_configured + LLM healthy → degraded."""
        settings = MagicMock()
        settings.openai_api_key = "sk-..."
        settings.anthropic_api_key = ""
        settings.openrouter_api_key = ""
        settings.local_llm_base_url = ""
        settings.llamacpp_base_url = ""
        settings.default_llm_provider = "openai"

        with patch("app.config.get_settings", return_value=settings):
            service = HealthService(
                db_session_factory=healthy_db,
                redis_url="",
                connector_manager=None,
            )
            overall = await service.check_all()

        assert overall.status == "degraded"
