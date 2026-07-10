"""Unit tests for ConnectorManager retry, backoff, circuit-breaker, and health-check logic.

Tests focus on the static/sync helpers (``_is_retryable``,
``_extract_retry_after``, ``_compute_backoff``, ``_record_success``,
``_record_failure``, ``_is_circuit_broken``) as well as the async
``_search_source`` and ``health_check`` composite methods.
"""

from __future__ import annotations

import asyncio
import json
import time as _time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.connectors.base import RawPaper, SearchQuery, SearchResult
from app.connectors.manager import (
    BASE_DELAY_SECONDS,
    CIRCUIT_BREAK_THRESHOLD,
    CIRCUIT_BREAK_TTL_SECONDS,
    JITTER_FACTOR,
    MAX_DELAY_SECONDS,
    ConnectorManager,
)


# ── Stub connector (same pattern as test_manager_cache.py) ──────────────


class StubConnector:
    """Minimal stub that returns a fixed search result on success."""

    def __init__(self, name: str = "stub"):
        self._name = name
        self.search_calls = 0

    @property
    def connector_name(self) -> str:
        return self._name

    @property
    def base_url(self) -> str:
        return f"https://{self._name}.example.com"

    async def search(self, query: SearchQuery) -> SearchResult:
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

    async def get_paper(self, identifier: str) -> RawPaper | None:
        return None

    async def get_citations(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        return []

    async def get_references(self, paper_id: str, limit: int = 20) -> list[RawPaper]:
        return []

    async def health_check(self) -> bool:
        return True


# ======================================================================
# _is_retryable — error classification
# ======================================================================


class TestIsRetryable:
    """Cover every branch of :meth:`ConnectorManager._is_retryable`."""

    # ── Retryable HTTP statuses ──────────────────────────────────────

    @pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
    def test_retryable_http_statuses(self, status: int) -> None:
        exc = httpx.HTTPStatusError(
            "msg", request=MagicMock(), response=MagicMock(status_code=status)
        )
        assert ConnectorManager._is_retryable(exc) is True

    # ── Non-retryable HTTP statuses ──────────────────────────────────

    @pytest.mark.parametrize("status", [400, 401, 403, 404, 405, 410, 422])
    def test_non_retryable_http_statuses(self, status: int) -> None:
        exc = httpx.HTTPStatusError(
            "msg", request=MagicMock(), response=MagicMock(status_code=status)
        )
        assert ConnectorManager._is_retryable(exc) is False

    # ── Non-HTTP retryable exceptions ────────────────────────────────

    def test_timeout_exception(self) -> None:
        exc = httpx.TimeoutException("timed out")
        assert ConnectorManager._is_retryable(exc) is True

    def test_connect_error(self) -> None:
        exc = httpx.ConnectError("connection refused")
        assert ConnectorManager._is_retryable(exc) is True

    def test_request_error_generic(self) -> None:
        exc = httpx.RequestError("generic network error")
        assert ConnectorManager._is_retryable(exc) is True

    # ── Non-retryable non-HTTP exceptions ────────────────────────────

    @pytest.mark.parametrize(
        "exc",
        [
            ValueError("bad value"),
            KeyError("missing key"),
            RuntimeError("unexpected"),
            TypeError("type mismatch"),
            json.JSONDecodeError("bad json", "", 0),
        ],
    )
    def test_non_retryable_non_http(self, exc: Exception) -> None:
        assert ConnectorManager._is_retryable(exc) is False


# ======================================================================
# _extract_retry_after — Retry-After header parsing
# ======================================================================


class TestExtractRetryAfter:
    """Cover :meth:`ConnectorManager._extract_retry_after`."""

    def test_non_429_returns_none(self) -> None:
        exc = httpx.HTTPStatusError(
            "msg", request=MagicMock(), response=MagicMock(status_code=503)
        )
        assert ConnectorManager._extract_retry_after(exc) is None

    def test_non_http_error_returns_none(self) -> None:
        exc = ValueError("some error")
        assert ConnectorManager._extract_retry_after(exc) is None

    def test_extracts_delta_seconds(self) -> None:
        response = MagicMock(status_code=429)
        response.headers = {"Retry-After": "5"}
        exc = httpx.HTTPStatusError("msg", request=MagicMock(), response=response)
        result = ConnectorManager._extract_retry_after(exc)
        assert result == 5.0

    def test_invalid_header_returns_none(self) -> None:
        response = MagicMock(status_code=429)
        response.headers = {"Retry-After": "not-a-number"}
        exc = httpx.HTTPStatusError("msg", request=MagicMock(), response=response)
        assert ConnectorManager._extract_retry_after(exc) is None

    def test_missing_header_returns_none(self) -> None:
        response = MagicMock(status_code=429)
        response.headers = {}
        exc = httpx.HTTPStatusError("msg", request=MagicMock(), response=response)
        assert ConnectorManager._extract_retry_after(exc) is None

    def test_http_date_header_returns_none(self) -> None:
        """HTTP-date format is not supported — returns None."""
        response = MagicMock(status_code=429)
        response.headers = {"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}
        exc = httpx.HTTPStatusError("msg", request=MagicMock(), response=response)
        assert ConnectorManager._extract_retry_after(exc) is None


# ======================================================================
# _compute_backoff — exponential backoff with jitter
# ======================================================================


class TestComputeBackoff:
    """Cover :meth:`ConnectorManager._compute_backoff`."""

    def _backoff(self, attempt: int, exc: Exception | None = None) -> float:
        """Helper: call instance method via a fresh manager."""
        return ConnectorManager()._compute_backoff(attempt=attempt, exc=exc)

    def test_minimum_floor(self) -> None:
        """Even with attempt=0 and no Retry-After, delay >= 0.1."""
        delay = self._backoff(attempt=0)
        assert delay >= 0.1

    def test_increases_with_attempt(self) -> None:
        """Higher attempts produce larger delays (at least ≥ base)."""
        d0 = self._backoff(attempt=0)
        d1 = self._backoff(attempt=1)
        d2 = self._backoff(attempt=2)
        # With jitter this isn't strictly monotonic, but should trend upward
        assert d1 > d0 * 0.5  # loose check
        assert d2 > d0 * 0.25

    def test_capped_at_max_delay(self) -> None:
        """Very high attempts are capped at MAX_DELAY_SECONDS (before jitter).

        After the cap is applied, jitter of ±25% can push the actual delay
        up to ``MAX_DELAY_SECONDS * (1 + JITTER_FACTOR)``.
        """
        delay = self._backoff(attempt=10)
        max_possible = MAX_DELAY_SECONDS * (1 + JITTER_FACTOR)
        assert delay <= max_possible

    def test_honours_retry_after(self) -> None:
        """Retry-After from a 429 is used as base."""
        response = MagicMock(status_code=429)
        response.headers = {"Retry-After": "3"}
        exc = httpx.HTTPStatusError("msg", request=MagicMock(), response=response)
        delay = self._backoff(attempt=0, exc=exc)
        assert delay >= 0.1
        assert delay < 20.0

    def test_jitter_produces_variation(self) -> None:
        """Multiple calls with the same args produce different values."""
        delays = {self._backoff(attempt=1) for _ in range(10)}
        assert len(delays) > 1, "jitter should produce non-deterministic values"


# ======================================================================
# Circuit-breaker: _record_success, _record_failure, _is_circuit_broken
# ======================================================================


class TestCircuitBreaker:
    """Cover the circuit-breaker state machine."""

    def test_record_success_resets_failures(self) -> None:
        manager = ConnectorManager()
        manager._connector_failures["arxiv"] = 3
        manager._connector_cooldown_until["arxiv"] = 12345.0

        manager._record_success("arxiv")
        assert "arxiv" not in manager._connector_failures
        assert "arxiv" not in manager._connector_cooldown_until

    def test_record_failure_increments(self) -> None:
        manager = ConnectorManager()
        manager._record_failure("arxiv")
        assert manager._connector_failures["arxiv"] == 1

        manager._record_failure("arxiv")
        assert manager._connector_failures["arxiv"] == 2

    def test_circuit_trips_at_threshold(self) -> None:
        manager = ConnectorManager()
        for _ in range(CIRCUIT_BREAK_THRESHOLD):
            manager._record_failure("arxiv")

        assert manager._connector_failures["arxiv"] == CIRCUIT_BREAK_THRESHOLD
        cooldown = manager._connector_cooldown_until.get("arxiv", 0.0)
        assert cooldown > _time.monotonic()
        assert cooldown <= _time.monotonic() + CIRCUIT_BREAK_TTL_SECONDS + 1

    def test_circuit_not_tripped_below_threshold(self) -> None:
        manager = ConnectorManager()
        for _ in range(CIRCUIT_BREAK_THRESHOLD - 1):
            manager._record_failure("arxiv")

        assert "arxiv" not in manager._connector_cooldown_until

    def test_is_circuit_broken_during_cooldown(self) -> None:
        manager = ConnectorManager()
        manager._connector_cooldown_until["arxiv"] = _time.monotonic() + 60.0
        assert manager._is_circuit_broken("arxiv") is True

    def test_is_circuit_broken_after_cooldown_expires(self) -> None:
        manager = ConnectorManager()
        manager._connector_cooldown_until["arxiv"] = _time.monotonic() - 1.0
        assert manager._is_circuit_broken("arxiv") is False

    def test_is_circuit_broken_no_state(self) -> None:
        manager = ConnectorManager()
        assert manager._is_circuit_broken("arxiv") is False


# ======================================================================
# _search_source — retry loop integration
# ======================================================================


class TestSearchSource:
    """Cover :meth:`ConnectorManager._search_source`."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self) -> None:
        manager = ConnectorManager()
        connector = StubConnector("working")
        manager.register_connector("working", connector)

        result = await manager._search_source("working", SearchQuery(text="test"))
        source_name, search_result = result
        assert source_name == "working"
        assert search_result is not None
        assert connector.search_calls == 1

    @pytest.mark.asyncio
    async def test_retries_on_retryable_http_error(self) -> None:
        class RetryOnceConnector(StubConnector):
            def __init__(self):
                super().__init__("retry-once")
                self.attempts = 0

            async def search(self, query):
                self.attempts += 1
                if self.attempts < 3:
                    raise httpx.HTTPStatusError(
                        "too many",
                        request=MagicMock(),
                        response=MagicMock(status_code=502),
                    )
                return await super().search(query)

        manager = ConnectorManager()
        connector = RetryOnceConnector()
        manager.register_connector("retry-once", connector)

        result = await manager._search_source("retry-once", SearchQuery(text="test"))
        source_name, search_result = result
        assert source_name == "retry-once"
        assert search_result is not None
        assert connector.attempts == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_non_retryable_http_error(self) -> None:
        class BadRequestConnector(StubConnector):
            def __init__(self):
                super().__init__("bad-request")
                self.attempts = 0

            async def search(self, query):
                self.attempts += 1
                raise httpx.HTTPStatusError(
                    "bad request",
                    request=MagicMock(),
                    response=MagicMock(status_code=400),
                )

        manager = ConnectorManager()
        connector = BadRequestConnector()
        manager.register_connector("bad-request", connector)

        result = await manager._search_source(
            "bad-request", SearchQuery(text="test")
        )
        source_name, search_result = result
        assert source_name == "bad-request"
        assert search_result is None
        assert connector.attempts == 1  # no retry

    @pytest.mark.asyncio
    async def test_gives_up_after_max_retries(self) -> None:
        class AlwaysFailingConnector(StubConnector):
            def __init__(self):
                super().__init__("always-fail")
                self.attempts = 0

            async def search(self, query):
                self.attempts += 1
                raise httpx.HTTPStatusError(
                    "server error",
                    request=MagicMock(),
                    response=MagicMock(status_code=503),
                )

        manager = ConnectorManager()
        connector = AlwaysFailingConnector()
        manager.register_connector("always-fail", connector)

        result = await manager._search_source(
            "always-fail", SearchQuery(text="test")
        )
        source_name, search_result = result
        assert source_name == "always-fail"
        assert search_result is None
        assert connector.attempts == 3  # all attempts exhausted

    @pytest.mark.asyncio
    async def test_respects_circuit_breaker(self) -> None:
        manager = ConnectorManager()
        connector = StubConnector("circuit-broken")
        manager.register_connector("circuit-broken", connector)
        manager._connector_cooldown_until["circuit-broken"] = (
            _time.monotonic() + 60.0
        )

        result = await manager._search_source(
            "circuit-broken", SearchQuery(text="test")
        )
        source_name, search_result = result
        assert source_name == "circuit-broken"
        assert search_result is None  # skipped due to open circuit
        assert connector.search_calls == 0

    @pytest.mark.asyncio
    async def test_unexpected_exception_not_retried(self) -> None:
        class ExplodingConnector(StubConnector):
            def __init__(self):
                super().__init__("explode")
                self.attempts = 0

            async def search(self, query):
                self.attempts += 1
                msg = "something completely unexpected"
                raise ValueError(msg)

        manager = ConnectorManager()
        connector = ExplodingConnector()
        manager.register_connector("explode", connector)

        result = await manager._search_source("explode", SearchQuery(text="test"))
        source_name, search_result = result
        assert source_name == "explode"
        assert search_result is None
        assert connector.attempts == 1  # not retried

    @pytest.mark.asyncio
    async def test_retry_on_network_error(self) -> None:
        class FlakyNetworkConnector(StubConnector):
            def __init__(self):
                super().__init__("flaky-net")
                self.attempts = 0

            async def search(self, query):
                self.attempts += 1
                if self.attempts < 2:
                    raise httpx.TimeoutException("connection timed out")
                return await super().search(query)

        manager = ConnectorManager()
        connector = FlakyNetworkConnector()
        manager.register_connector("flaky-net", connector)

        result = await manager._search_source("flaky-net", SearchQuery(text="test"))
        source_name, search_result = result
        assert source_name == "flaky-net"
        assert search_result is not None
        assert connector.attempts == 2

    @pytest.mark.asyncio
    async def test_network_error_gives_up_after_max_retries(self) -> None:
        class DeadNetworkConnector(StubConnector):
            def __init__(self):
                super().__init__("dead-net")
                self.attempts = 0

            async def search(self, query):
                self.attempts += 1
                raise httpx.ConnectError("connection refused")

        manager = ConnectorManager()
        connector = DeadNetworkConnector()
        manager.register_connector("dead-net", connector)

        result = await manager._search_source("dead-net", SearchQuery(text="test"))
        assert result[1] is None
        assert connector.attempts == 3


# ======================================================================
# health_check — latency timing and error isolation
# ======================================================================


class TestHealthCheck:
    """Cover :meth:`ConnectorManager.health_check`."""

    @pytest.mark.asyncio
    async def test_all_healthy(self) -> None:
        manager = ConnectorManager()
        manager.register_connector("a", StubConnector("a"))
        manager.register_connector("b", StubConnector("b"))

        results = await manager.health_check()
        assert "a" in results
        assert "b" in results
        for entry in results.values():
            assert entry["online"] is True
            assert entry["latency_ms"] >= 0

    @pytest.mark.asyncio
    async def test_failed_connector_is_not_online(self) -> None:
        class BrokenConnector(StubConnector):
            async def health_check(self) -> bool:
                msg = "API unavailable"
                raise RuntimeError(msg)

        manager = ConnectorManager()
        manager.register_connector("broken", BrokenConnector("broken"))
        manager.register_connector("ok", StubConnector("ok"))

        results = await manager.health_check()
        assert results["broken"]["online"] is False
        assert results["broken"]["latency_ms"] >= 0
        assert results["ok"]["online"] is True

    @pytest.mark.asyncio
    async def test_empty_manager_returns_empty_dict(self) -> None:
        manager = ConnectorManager()
        results = await manager.health_check()
        assert results == {}

    @pytest.mark.asyncio
    async def test_latency_is_recorded(self) -> None:
        class SlowConnector(StubConnector):
            async def health_check(self) -> bool:
                await asyncio.sleep(0.01)  # 10ms
                return True

        manager = ConnectorManager()
        manager.register_connector("slow", SlowConnector("slow"))

        results = await manager.health_check()
        assert results["slow"]["online"] is True
        assert results["slow"]["latency_ms"] >= 5  # at least ~5ms

    @pytest.mark.asyncio
    async def test_failure_does_not_crash_other_connectors(self) -> None:
        class ExplodingConnector(StubConnector):
            async def health_check(self) -> bool:
                msg = "kaboom"
                raise RuntimeError(msg)

        manager = ConnectorManager()
        manager.register_connector("explode", ExplodingConnector("explode"))
        manager.register_connector("ok", StubConnector("ok"))

        results = await manager.health_check()
        assert "explode" in results
        assert results["explode"]["online"] is False
        assert results["ok"]["online"] is True


# ======================================================================
# health_check — circuit-breaker state propagation
# ======================================================================


class TestHealthCheckCircuitBreaker:
    """Cover circuit-breaker state (``closed``/``half_open``/``open``)
    and ``failure_count`` / ``cooldown_remaining`` fields in
    :meth:`ConnectorManager.health_check`."""

    @pytest.mark.asyncio
    async def test_closed_state_no_failures(self) -> None:
        """No failures recorded → circuit_breaker='closed', failure_count=0."""
        manager = ConnectorManager()
        manager.register_connector("ok", StubConnector("ok"))

        results = await manager.health_check()
        assert results["ok"]["circuit_breaker"] == "closed"
        assert results["ok"]["failure_count"] == 0
        assert results["ok"]["cooldown_remaining"] == 0.0

    @pytest.mark.asyncio
    async def test_prior_failures_without_cooldown_produces_half_open(self) -> None:
        """Failures > 0 but cooldown expired → circuit_breaker='half_open'.

        The state machine: if cooldown is not active (no open circuit)
        but failures have been recorded, the connector is in "half_open"
        (recovering) state.  Only when *both* cooldown and failures are
        cleared does the state return to ``closed``.
        """
        manager = ConnectorManager()
        manager.register_connector("ok", StubConnector("ok"))
        manager._connector_failures["ok"] = 2
        manager._connector_cooldown_until["ok"] = _time.monotonic() - 10.0

        results = await manager.health_check()
        assert results["ok"]["circuit_breaker"] == "half_open"
        assert results["ok"]["failure_count"] == 2
        assert results["ok"]["cooldown_remaining"] == 0.0

    @pytest.mark.asyncio
    async def test_half_open_failures_exist_cooldown_expired(self) -> None:
        """failures > 0, cooldown expired → circuit_breaker='half_open'."""
        manager = ConnectorManager()
        manager.register_connector("recovering", StubConnector("recovering"))
        manager._connector_failures["recovering"] = 3
        manager._connector_cooldown_until["recovering"] = _time.monotonic() - 1.0

        results = await manager.health_check()
        assert results["recovering"]["circuit_breaker"] == "half_open"
        assert results["recovering"]["failure_count"] == 3
        assert results["recovering"]["cooldown_remaining"] == 0.0

    @pytest.mark.asyncio
    async def test_open_cooldown_active(self) -> None:
        """Cooldown active → circuit_breaker='open', cooldown_remaining > 0."""
        manager = ConnectorManager()
        manager.register_connector("tripped", StubConnector("tripped"))
        manager._connector_failures["tripped"] = 5
        now = _time.monotonic()
        manager._connector_cooldown_until["tripped"] = now + 30.0

        results = await manager.health_check()
        assert results["tripped"]["circuit_breaker"] == "open"
        assert results["tripped"]["failure_count"] == 5
        remaining = results["tripped"]["cooldown_remaining"]
        assert isinstance(remaining, float)
        assert remaining > 0.0
        # Should be ~30s minus elapsed time (allow generous ±1s tolerance)
        assert 28.0 <= remaining <= 31.0

    @pytest.mark.asyncio
    async def test_open_reports_cooldown_accurately(self) -> None:
        """cooldown_remaining reflects the real time left within tolerance."""
        manager = ConnectorManager()
        manager.register_connector("hot", StubConnector("hot"))
        now = _time.monotonic()
        manager._connector_cooldown_until["hot"] = now + 5.0

        results = await manager.health_check()
        remaining = results["hot"]["cooldown_remaining"]
        # ~5s minus elapsed — should still be positive and ≤5
        assert remaining > 0.0
        assert remaining <= 5.5

    @pytest.mark.asyncio
    async def test_open_isolation_on_health_check_failure(self) -> None:
        """When connector.health_check() raises, open-state fields survive."""
        class BrokenConnector(StubConnector):
            async def health_check(self) -> bool:
                msg = "API unavailable"
                raise RuntimeError(msg)

        manager = ConnectorManager()
        manager.register_connector("broken", BrokenConnector("broken"))
        manager._connector_failures["broken"] = 5
        now = _time.monotonic()
        manager._connector_cooldown_until["broken"] = now + 60.0

        results = await manager.health_check()
        assert results["broken"]["online"] is False
        assert results["broken"]["circuit_breaker"] == "open"
        assert results["broken"]["failure_count"] == 5
        assert results["broken"]["cooldown_remaining"] > 0.0

    @pytest.mark.asyncio
    async def test_half_open_with_health_check_failure(self) -> None:
        """Half-open connector that fails its probe still shows half-open state."""
        class BrokenConnector(StubConnector):
            async def health_check(self) -> bool:
                msg = "still recovering"
                raise RuntimeError(msg)

        manager = ConnectorManager()
        manager.register_connector("shaky", BrokenConnector("shaky"))
        manager._connector_failures["shaky"] = 3
        manager._connector_cooldown_until["shaky"] = _time.monotonic() - 5.0

        results = await manager.health_check()
        assert results["shaky"]["online"] is False
        assert results["shaky"]["circuit_breaker"] == "half_open"
        assert results["shaky"]["failure_count"] == 3
        assert results["shaky"]["cooldown_remaining"] == 0.0

    @pytest.mark.asyncio
    async def test_connector_without_state_defaults_closed(self) -> None:
        """Connector with no circuit-breaker records at all defaults to closed."""
        manager = ConnectorManager()
        manager.register_connector("clean", StubConnector("clean"))
        # Deliberately NOT setting any circuit-breaker state

        results = await manager.health_check()
        assert results["clean"]["circuit_breaker"] == "closed"
        assert results["clean"]["failure_count"] == 0
        assert results["clean"]["cooldown_remaining"] == 0.0


