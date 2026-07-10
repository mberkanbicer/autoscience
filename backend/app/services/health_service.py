"""Aggregated health-checks for database, Redis, LLM providers, and connectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog
from sqlalchemy import text

logger = structlog.get_logger()


@dataclass
class HealthResult:
    """Result of a single health check."""

    status: str  # "healthy" | "unhealthy" | "not_configured" | "not_available"
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class OverallHealth:
    """Aggregated health of all checked services."""

    status: str  # "healthy" | "degraded" | "unhealthy"
    version: str = "0.1.0"
    checks: dict[str, HealthResult] = field(default_factory=dict)


class HealthService:
    """Run health checks against the system's external dependencies."""

    def __init__(
        self,
        db_session_factory=None,
        redis_url: str = "",
        connector_manager=None,
    ):
        self.db_factory = db_session_factory
        self.redis_url = redis_url
        self.connector_manager = connector_manager

    # ── Database ────────────────────────────────────────────────────────

    async def check_database(self) -> HealthResult:
        try:
            if not self.db_factory:
                return HealthResult(status="not_configured", error="No DB session factory provided")
            async with self.db_factory() as session:
                await session.execute(text("SELECT 1"))
            return HealthResult(status="healthy")
        except Exception as exc:
            logger.warning("health_db_failed", error=str(exc))
            return HealthResult(status="unhealthy", error=str(exc)[:300])

    # ── Redis ───────────────────────────────────────────────────────────

    async def check_redis(self) -> HealthResult:
        if not self.redis_url:
            return HealthResult(status="not_configured", error="REDIS_URL not set")
        try:
            from redis.asyncio import Redis

            client = Redis.from_url(self.redis_url, socket_timeout=3, decode_responses=True)
            await client.ping()
            info = await client.info("server")
            await client.aclose()
            return HealthResult(
                status="healthy",
                details={
                    "redis_version": info.get("redis_version", "unknown"),
                },
            )
        except Exception as exc:
            logger.warning("health_redis_failed", error=str(exc))
            return HealthResult(status="unhealthy", error=str(exc)[:300])

    # ── LLM Providers ───────────────────────────────────────────────────

    async def check_llm(self) -> HealthResult:
        try:
            from app.config import get_settings

            settings = get_settings()
        except Exception as exc:
            return HealthResult(status="unhealthy", error=f"Cannot load settings: {exc}")

        providers: dict[str, dict[str, Any]] = {}

        # Check each provider by API key presence
        if settings.openai_api_key:
            providers["openai"] = {
                "configured": True,
                "default_model": settings.openai_default_model,
            }
        else:
            providers["openai"] = {"configured": False}

        if settings.anthropic_api_key:
            providers["anthropic"] = {
                "configured": True,
                "default_model": settings.anthropic_default_model,
            }
        else:
            providers["anthropic"] = {"configured": False}

        if settings.openrouter_api_key:
            providers["openrouter"] = {
                "configured": True,
                "default_model": settings.openrouter_default_model,
            }
        else:
            providers["openrouter"] = {"configured": False}

        if settings.local_llm_base_url:
            providers["local"] = {
                "configured": True,
                "base_url": settings.local_llm_base_url,
                "model": settings.local_llm_model,
            }
        else:
            providers["local"] = {"configured": False}

        if settings.llamacpp_base_url:
            providers["llamacpp"] = {
                "configured": True,
                "base_url": settings.llamacpp_base_url,
                "model": settings.llamacpp_model,
            }
        else:
            providers["llamacpp"] = {"configured": False}

        configured_count = sum(1 for p in providers.values() if p.get("configured"))
        if configured_count == 0:
            return HealthResult(
                status="degraded",
                error="No LLM providers configured — set an API key",
                details={"providers": providers, "configured_count": 0, "default": settings.default_llm_provider},
            )

        return HealthResult(
            status="healthy",
            details={
                "providers": providers,
                "configured_count": configured_count,
                "default": settings.default_llm_provider,
            },
        )

    # ── Connectors ──────────────────────────────────────────────────────

    async def check_connectors(self) -> HealthResult:
        if not self.connector_manager:
            return HealthResult(status="not_available", error="No connector manager available")

        try:
            raw = await self.connector_manager.health_check()

            # Normalise mixed bool/dict results to a uniform dict format
            per_connector: dict[str, dict] = {}
            for name, val in raw.items():
                if isinstance(val, dict):
                    per_connector[name] = val
                else:
                    # Legacy boolean-only response
                    per_connector[name] = {"online": bool(val), "latency_ms": None}

            healthy_count = sum(1 for v in per_connector.values() if v.get("online"))
            total = len(per_connector)

            # Compute average latency from connectors with timing data
            latencies = [
                v["latency_ms"]
                for v in per_connector.values()
                if v.get("latency_ms") is not None
            ]
            avg_latency_ms = round(sum(latencies) / len(latencies), 1) if latencies else None

            details: dict[str, Any] = {
                "healthy": healthy_count,
                "total": total,
                "per_connector": per_connector,
            }
            if avg_latency_ms is not None:
                details["avg_latency_ms"] = avg_latency_ms

            if healthy_count == total:
                return HealthResult(status="healthy", details=details)
            return HealthResult(
                status="degraded",
                details=details,
                error=f"{healthy_count}/{total} connectors healthy",
            )
        except Exception as exc:
            logger.warning("health_connectors_failed", error=str(exc))
            return HealthResult(status="unhealthy", error=str(exc)[:300])

    # ── Aggregate ───────────────────────────────────────────────────────

    async def check_all(self) -> OverallHealth:
        """Run all health checks and return an aggregated summary."""
        db = await self.check_database()
        redis = await self.check_redis()
        llm = await self.check_llm()
        connectors = await self.check_connectors()

        results = {
            "database": db,
            "redis": redis,
            "llm": llm,
            "connectors": connectors,
        }

        # Overall status: all healthy → healthy, any unhealthy → unhealthy, else degraded
        statuses = [r.status for r in results.values()]
        if all(s == "healthy" for s in statuses):
            overall = "healthy"
        elif any(s == "unhealthy" for s in statuses):
            overall = "unhealthy"
        else:
            overall = "degraded"

        return OverallHealth(status=overall, version="0.1.0", checks=results)
