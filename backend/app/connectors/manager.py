"""Academic source connector manager with retry, backoff, and circuit-breaker."""

import asyncio
import random
import time as _time

import httpx
import structlog

from app.services.cache_service import CacheService

from .arxiv import ArxivConnector
from .base import (
    DEFAULT_LIMITS,
    DEFAULT_TIMEOUT,
    AcademicConnector,
    RawPaper,
    SearchQuery,
    SearchResult,
)
from .core import COREConnector
from .crossref import CrossrefConnector
from .doaj import DOAJConnector
from .firecrawl import FirecrawlConnector
from .openalex import OpenAlexConnector
from .pubmed import PubMedConnector
from .searxng import SearXNGConnector
from .semantic_scholar import SemanticScholarConnector
from .serialization import (
    paper_from_dict,
    paper_to_dict,
    search_result_from_dict,
    search_result_to_dict,
)
from .unpaywall import UnpaywallConnector

# ── Shared connector HTTP configuration (re-exported for clarity) ─────
# These constants are the authoritative defaults; connector implementations
# should call ``create_connector_client()`` from base.py rather than
# constructing ``httpx.AsyncClient`` directly.
CONNECTOR_TIMEOUT = DEFAULT_TIMEOUT
CONNECTOR_LIMITS = DEFAULT_LIMITS


logger = structlog.get_logger()


# ── Retry & circuit-breaker configuration ──────────────────────────────

# Maximum number of retry attempts per request (1 initial + N-1 retries)
MAX_RETRIES = 3

# Base delay in seconds before the first retry
BASE_DELAY_SECONDS = 0.5

# Maximum delay between retries (cap the exponential growth)
MAX_DELAY_SECONDS = 15.0

# Jitter factor: actual_delay = delay * random.uniform(1-JITTER, 1+JITTER)
JITTER_FACTOR = 0.25

# Circuit-breaker: after this many consecutive failures the connector is
# skipped for CIRCUIT_BREAK_TTL seconds
CIRCUIT_BREAK_THRESHOLD = 5
CIRCUIT_BREAK_TTL_SECONDS = 60.0

# HTTP status codes that are safe to retry
_RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})

# HTTP status codes that are definitively non-retryable (auth, bad request, not found)
_NON_RETRYABLE_STATUSES = frozenset({400, 401, 403, 404, 405, 410, 422})


class ConnectorManager:
    """Manager for multiple academic source connectors."""

    def __init__(self, cache_service: CacheService | None = None, cache_ttl_seconds: int = 3600):
        self.connectors: dict[str, AcademicConnector] = {}
        self.cache = cache_service
        self.cache_ttl_seconds = cache_ttl_seconds
        self.optional_connectors: dict[str, dict[str, bool | str]] = {}

        # Circuit-breaker state: connector_name -> consecutive_failure_count
        self._connector_failures: dict[str, int] = {}
        # Circuit-breaker cool-down: connector_name -> timestamp until which to skip
        self._connector_cooldown_until: dict[str, float] = {}

    def register_connector(self, name: str, connector: AcademicConnector) -> None:
        """Register a connector."""
        self.connectors[name] = connector
        logger.info("connector_registered", connector=name)

    def get_connector(self, name: str) -> AcademicConnector:
        """Get a connector by name."""
        if name not in self.connectors:
            raise ValueError(f"Connector {name} not registered")
        return self.connectors[name]

    def _cache_key(self, query: SearchQuery, sources: list[str] | None) -> dict:
        return {
            "text": query.text,
            "year_from": query.year_from,
            "year_to": query.year_to,
            "limit": query.limit,
            "paper_type": query.paper_type,
            "sort_by": query.sort_by,
            "sources": sorted(sources or list(self.connectors.keys())),
        }

    @staticmethod
    def _extract_retry_after(exc: Exception) -> float | None:
        """Extract ``Retry-After`` header value (seconds) from a 429 response."""
        if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
            raw = exc.response.headers.get("Retry-After")
            if raw is not None:
                try:
                    # Retry-After can be a delta-seconds integer or an HTTP-date
                    return float(raw)
                except (ValueError, TypeError):
                    pass
        return None

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        """Return True if *exc* represents a transient failure worth retrying.

        Retryable:
        - ``httpx.HTTPStatusError`` with status 429, 5xx
        - ``httpx.TimeoutException``
        - ``httpx.ConnectError`` (connection refused, DNS failure)
        - ``httpx.RequestError`` (network-level errors)

        Non-retryable:
        - ``httpx.HTTPStatusError`` with status 400, 401, 403, 404, 405, 410, 422
        - ``json.JSONDecodeError`` (response is not valid JSON — unlikely
          to succeed on retry with the same URL)
        - ``ET.ParseError`` (malformed XML — same URL will produce same XML)
        """
        if isinstance(exc, httpx.HTTPStatusError):
            sc = exc.response.status_code
            if sc in _NON_RETRYABLE_STATUSES:
                return False
            return sc in _RETRYABLE_STATUSES
        if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.RequestError)):
            return True
        return False

    def _is_circuit_broken(self, source_name: str) -> bool:
        """Check whether *source_name* is in circuit-breaker cool-down."""
        cooldown_until = self._connector_cooldown_until.get(source_name, 0.0)
        if cooldown_until > _time.monotonic():
            logger.warning("connector_circuit_broken", source=source_name)
            return True
        return False

    def _record_success(self, source_name: str) -> None:
        """Reset failure counter on success."""
        self._connector_failures.pop(source_name, None)
        self._connector_cooldown_until.pop(source_name, None)

    def _record_failure(self, source_name: str) -> None:
        """Increment failure counter and trip breaker if threshold exceeded."""
        count = self._connector_failures.get(source_name, 0) + 1
        self._connector_failures[source_name] = count

        if count >= CIRCUIT_BREAK_THRESHOLD:
            self._connector_cooldown_until[source_name] = _time.monotonic() + CIRCUIT_BREAK_TTL_SECONDS
            logger.error(
                "connector_circuit_opened",
                source=source_name,
                consecutive_failures=count,
                cooldown_seconds=CIRCUIT_BREAK_TTL_SECONDS,
            )

    def reset_circuit_breaker(self, source_name: str) -> dict[str, bool | str]:
        """Manually reset the circuit-breaker for a connector.

        Clears the failure counter and cooldown timer so the next
        request will be allowed through immediately.

        Args:
            source_name: The connector name to reset.

        Returns:
            A dict with ``success`` and ``previous_state`` keys.

        Raises:
            ValueError: If ``source_name`` is not a registered connector.

        """
        if source_name not in self.connectors:
            raise ValueError(f"Connector '{source_name}' not registered")

        # Determine previous state before clearing
        failures = self._connector_failures.get(source_name, 0)
        cooldown_until = self._connector_cooldown_until.get(source_name, 0.0)
        now = _time.monotonic()

        if cooldown_until > now:
            previous_state = "open"
        elif failures > 0:
            previous_state = "half_open"
        else:
            previous_state = "closed"

        self._connector_failures.pop(source_name, None)
        self._connector_cooldown_until.pop(source_name, None)

        logger.info(
            "connector_circuit_reset",
            source=source_name,
            previous_state=previous_state,
            previous_failures=failures,
        )

        return {
            "success": True,
            "source": source_name,
            "previous_state": previous_state,
        }

    def _compute_backoff(self, attempt: int, exc: Exception | None = None) -> float:
        """Compute the retry delay with exponential backoff, jitter, and rate-limit awareness.

        When a 429 response carries a ``Retry-After`` header, that value
        is used as the base delay (capped by ``MAX_DELAY_SECONDS``).
        Otherwise the standard exponential formula is applied.
        """
        # Honour Retry-After from 429 responses
        retry_after = self._extract_retry_after(exc) if exc else None
        if retry_after is not None:
            base = min(retry_after + random.uniform(0, 2.0), MAX_DELAY_SECONDS)
        else:
            base = BASE_DELAY_SECONDS * (2 ** attempt)
            base = min(base, MAX_DELAY_SECONDS)

        jitter = base * JITTER_FACTOR
        actual = base + random.uniform(-jitter, jitter)
        return max(0.1, actual)

    async def _search_source(
        self,
        source_name: str,
        query: SearchQuery,
    ) -> tuple[str, SearchResult | None]:
        """Search a single connector with exponential backoff, jitter, and circuit-breaker."""
        if self._is_circuit_broken(source_name):
            return source_name, None

        connector = self.connectors[source_name]

        for attempt in range(MAX_RETRIES):
            try:
                result = await connector.search(query)
                self._record_success(source_name)
                return source_name, result

            except asyncio.CancelledError:
                raise
            except KeyboardInterrupt:
                raise
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                if attempt == MAX_RETRIES - 1:
                    logger.error(
                        "search_failed_network",
                        source=source_name,
                        error=str(exc),
                        attempt=attempt + 1,
                    )
                    self._record_failure(source_name)
                    return source_name, None

                delay = self._compute_backoff(attempt, exc)
                logger.warning(
                    "search_retry_network",
                    source=source_name,
                    attempt=attempt + 1,
                    delay_seconds=round(delay, 2),
                    error=str(exc)[:200],
                )
                await asyncio.sleep(delay)

            except httpx.HTTPStatusError as exc:
                sc = exc.response.status_code
                if sc not in _RETRYABLE_STATUSES or attempt == MAX_RETRIES - 1:
                    logger.error(
                        "search_failed_http",
                        source=source_name,
                        status_code=sc,
                        error=str(exc)[:200],
                        attempt=attempt + 1,
                    )
                    self._record_failure(source_name)
                    return source_name, None

                delay = self._compute_backoff(attempt, exc)
                logger.warning(
                    "search_retry_http",
                    source=source_name,
                    status_code=sc,
                    attempt=attempt + 1,
                    delay_seconds=round(delay, 2),
                )
                await asyncio.sleep(delay)

            except Exception as exc:
                # Non-HTTP unexpected errors — not retryable
                logger.error(
                    "search_failed_unexpected",
                    source=source_name,
                    error=str(exc),
                    attempt=attempt + 1,
                )
                self._record_failure(source_name)
                return source_name, None

        return source_name, None

    async def search_all(
        self,
        query: SearchQuery,
        sources: list[str] | None = None,
        *,
        force_refresh: bool = False,
    ) -> dict[str, SearchResult]:
        """Search across multiple sources in parallel with optional caching."""
        sources_to_search = sources or list(self.connectors.keys())
        cache_kwargs = self._cache_key(query, sources_to_search)

        if self.cache:
            cached, hit = await self.cache.get(
                "connector_search",
                force_refresh=force_refresh,
                **cache_kwargs,
            )
            if hit and cached:
                return {
                    name: search_result_from_dict(payload)
                    for name, payload in cached.items()
                }

        tasks = [
            self._search_source(source_name, query)
            for source_name in sources_to_search
            if source_name in self.connectors
        ]
        pairs = await asyncio.gather(*tasks) if tasks else []

        results: dict[str, SearchResult] = {}
        for source_name, result in pairs:
            if result is not None:
                results[source_name] = result
            elif source_name not in self.connectors:
                logger.warning("connector_not_found", source=source_name)

        if self.cache and results:
            serialized = {name: search_result_to_dict(result) for name, result in results.items()}
            await self.cache.set(
                "connector_search",
                serialized,
                ttl_seconds=self.cache_ttl_seconds,
                **cache_kwargs,
            )

        return results

    async def search_and_merge(
        self,
        query: SearchQuery,
        sources: list[str] | None = None,
        *,
        force_refresh: bool = False,
    ) -> list[RawPaper]:
        """Search and merge results from multiple sources."""
        merge_cache_kwargs = {
            **self._cache_key(query, sources),
            "merged": True,
        }

        if self.cache:
            cached, hit = await self.cache.get(
                "literature_merge",
                force_refresh=force_refresh,
                **merge_cache_kwargs,
            )
            if hit and cached:
                return [paper_from_dict(item) for item in cached]

        results = await self.search_all(query, sources, force_refresh=force_refresh)

        all_papers: list[RawPaper] = []
        seen_dois: set[str] = set()
        seen_titles: set[str] = set()

        for result in results.values():
            for paper in result.papers:
                if paper.doi and paper.doi in seen_dois:
                    continue

                normalized_title = paper.title.lower().strip()
                if normalized_title in seen_titles:
                    continue

                if paper.doi:
                    seen_dois.add(paper.doi)
                seen_titles.add(normalized_title)
                all_papers.append(paper)

        all_papers.sort(key=lambda p: p.citation_count or 0, reverse=True)

        if self.cache and all_papers:
            await self.cache.set(
                "literature_merge",
                [paper_to_dict(paper) for paper in all_papers],
                ttl_seconds=self.cache_ttl_seconds,
                **merge_cache_kwargs,
            )

        return all_papers

    async def get_paper(
        self,
        identifier: str,
        sources: list[str] | None = None,
    ) -> RawPaper | None:
        """Get a paper from multiple sources, respecting circuit-breakers."""
        sources_to_search = sources or list(self.connectors.keys())

        for source_name in sources_to_search:
            if source_name not in self.connectors:
                continue

            if self._is_circuit_broken(source_name):
                continue

            try:
                connector = self.connectors[source_name]
                paper = await connector.get_paper(identifier)
                if paper:
                    self._record_success(source_name)
                    return paper
                # Empty result from a live connector is not a failure
            except asyncio.CancelledError:
                raise
            except KeyboardInterrupt:
                raise
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                logger.warning("get_paper_network_error", source=source_name, error=str(exc))
                self._record_failure(source_name)
            except httpx.HTTPStatusError as exc:
                sc = exc.response.status_code
                if sc in _RETRYABLE_STATUSES:
                    logger.warning("get_paper_retryable_http", source=source_name, status_code=sc)
                    self._record_failure(source_name)
                else:
                    logger.warning("get_paper_http_error", source=source_name, status_code=sc, error=str(exc)[:200])
            except Exception as exc:
                logger.error("get_paper_failed", source=source_name, error=str(exc))
                self._record_failure(source_name)

        return None

    async def health_check(self) -> dict[str, dict | bool]:
        """Check health of all connectors with latency timing and circuit-breaker state.

        Returns a dict mapping connector name to either a boolean
        (legacy simple status) or a dict with ``online``,
        ``latency_ms``, ``circuit_breaker``, ``failure_count``,
        and ``cooldown_remaining`` keys when timing information
        is available.
        """
        results: dict[str, dict | bool] = {}
        now = _time.monotonic()
        for name, connector in self.connectors.items():
            start = now

            # Circuit-breaker state for this connector
            failures = self._connector_failures.get(name, 0)
            cooldown_until = self._connector_cooldown_until.get(name, 0.0)
            is_open = cooldown_until > now

            if is_open:
                circuit_state = "open"
            elif failures > 0:
                circuit_state = "half_open"
            else:
                circuit_state = "closed"

            cooldown_remaining = round(cooldown_until - now, 1) if is_open else 0.0

            try:
                ok = await connector.health_check()
                elapsed_ms = round((_time.monotonic() - start) * 1000, 1)
                results[name] = {
                    "online": ok,
                    "latency_ms": elapsed_ms,
                    "circuit_breaker": circuit_state,
                    "failure_count": failures,
                    "cooldown_remaining": cooldown_remaining,
                }
            except Exception as exc:
                elapsed_ms = round((_time.monotonic() - start) * 1000, 1)
                results[name] = {
                    "online": False,
                    "latency_ms": elapsed_ms,
                    "circuit_breaker": circuit_state,
                    "failure_count": failures,
                    "cooldown_remaining": cooldown_remaining,
                }
                logger.warning("connector_health_check_failed", source=name, latency_ms=elapsed_ms, error=str(exc), exc_info=True)
        return results


def create_default_manager(
    openalex_email: str | None = None,
    semantic_scholar_api_key: str | None = None,
    pubmed_api_key: str | None = None,
    core_api_key: str | None = None,
    unpaywall_email: str | None = None,
    searxng_url: str | None = None,
    firecrawl_api_key: str | None = None,
    cache_service: CacheService | None = None,
    cache_ttl_seconds: int = 3600,
) -> ConnectorManager:
    """Create a connector manager with default connectors."""
    manager = ConnectorManager(cache_service=cache_service, cache_ttl_seconds=cache_ttl_seconds)

    # Always-registered connectors
    manager.register_connector("openalex", OpenAlexConnector(email=openalex_email))
    manager.register_connector("semantic_scholar", SemanticScholarConnector(api_key=semantic_scholar_api_key))
    manager.register_connector("crossref", CrossrefConnector(email=openalex_email))
    manager.register_connector("arxiv", ArxivConnector())
    manager.register_connector("pubmed", PubMedConnector(api_key=pubmed_api_key))
    manager.register_connector("doaj", DOAJConnector())

    # Optional: CORE (requires API key)
    if core_api_key:
        manager.register_connector("core", COREConnector(api_key=core_api_key))
        manager.optional_connectors["core"] = {"configured": True, "registered": True}
    else:
        manager.optional_connectors["core"] = {
            "configured": False, "registered": False,
            "reason": "CORE_API_KEY not set",
        }

    # Optional: Unpaywall (requires email)
    if unpaywall_email and "@" in unpaywall_email:
        manager.register_connector("unpaywall", UnpaywallConnector(email=unpaywall_email))
        manager.optional_connectors["unpaywall"] = {"configured": True, "registered": True}
    else:
        manager.optional_connectors["unpaywall"] = {
            "configured": False, "registered": False,
            "reason": "UNPAYWALL_EMAIL not set or invalid",
        }

    if searxng_url:
        manager.register_connector(
            "searxng",
            SearXNGConnector(base_url=searxng_url, cache_service=cache_service),
        )
        manager.optional_connectors["searxng"] = {"configured": True, "registered": True}
    else:
        manager.optional_connectors["searxng"] = {
            "configured": False, "registered": False,
            "reason": "SEARXNG_URL not set",
        }

    if firecrawl_api_key:
        manager.register_connector(
            "firecrawl",
            FirecrawlConnector(api_key=firecrawl_api_key, cache_service=cache_service),
        )
        manager.optional_connectors["firecrawl"] = {"configured": True, "registered": True}
    else:
        manager.optional_connectors["firecrawl"] = {
            "configured": False, "registered": False,
            "reason": "FIRECRAWL_API_KEY not set",
        }

    return manager
