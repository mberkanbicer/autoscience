"""Periodic background health monitor: polls /health, tracks state transitions, and alerts on degradation."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger()

# ── Module-level lifecycle state ───────────────────────────────────────
_health_monitor_task: asyncio.Task | None = None
_previous_check_results: dict[str, str] = {}  # service_name -> last-known status


# ── Lifecycle ──────────────────────────────────────────────────────────

async def start_health_monitor(
    db_factory,
    interval_minutes: int = 5,
) -> asyncio.Task | None:
    """Start the background health monitor.

    Args:
        db_factory: Async session factory for DB health checks.
        interval_minutes: How often to poll health checks.

    Returns:
        The created asyncio.Task, or ``None`` if already running.

    """
    global _health_monitor_task

    if _health_monitor_task and not _health_monitor_task.done():
        logger.info("health_monitor_already_running")
        return None

    async def _run_loop():
        logger.info("health_monitor_started", interval_minutes=interval_minutes)

        # Run first check immediately on startup
        await _run_check(db_factory)

        while True:
            try:
                await asyncio.sleep(interval_minutes * 60)
                await _run_check(db_factory)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("health_monitor_loop_error", error=str(exc))

    _health_monitor_task = asyncio.create_task(_run_loop())
    return _health_monitor_task


async def stop_health_monitor() -> None:
    """Stop the background health monitor."""
    global _health_monitor_task
    if _health_monitor_task and not _health_monitor_task.done():
        _health_monitor_task.cancel()
        try:
            await _health_monitor_task
        except asyncio.CancelledError:
            pass
        _health_monitor_task = None
        logger.info("health_monitor_stopped")


def get_monitor_status() -> dict[str, Any]:
    """Return current monitor status (useful for diagnostics)."""
    return {
        "running": _health_monitor_task is not None and not _health_monitor_task.done(),
        "cached_service_statuses": dict(_previous_check_results),
    }


# ── Core check logic ───────────────────────────────────────────────────

def _should_alert(service_name: str, current_status: str) -> tuple[bool, str]:
    """Determine whether an alert should fire and what the previous status was.

    Only alerts on state transitions *toward* worse health:
      - healthy  → degraded  (alert)
      - healthy  → unhealthy (alert)
      - degraded → unhealthy (alert)
    """
    previous = _previous_check_results.get(service_name)

    # First-ever check — record silently, do not alert
    if previous is None:
        return False, previous or "unknown"

    # No transition
    if previous == current_status:
        return False, previous

    # Transition toward worse health
    if previous == "healthy" and current_status in ("degraded", "unhealthy"):
        return True, previous
    if previous == "degraded" and current_status == "unhealthy":
        return True, previous

    # Recovery (unhealthy→degraded, unhealthy→healthy, degraded→healthy)
    # or non-standard status ("not_configured", "not_available"):
    # log but do not send notification
    return False, previous


def _build_alert_body(overall, alerts: list[dict[str, Any]]) -> str:
    """Build a plain-text alert email body."""
    lines = [
        f"Health check at: {datetime.now(UTC).isoformat()}",
        f"Overall status: {overall.status}",
        "",
        "Degraded services:",
    ]
    for a in alerts:
        lines.append(
            f"  - {a['service']}: {a['previous_status']} → {a['current_status']}",
        )
        if a.get("error"):
            lines.append(f"    Error: {a['error']}")
    lines.extend(["", "All service statuses:"])
    for svc_name, result in overall.checks.items():
        lines.append(f"  {svc_name}: {result.status}")
    return "\n".join(lines)


async def _run_check(db_factory) -> None:
    """Execute one round of health checks and handle state transitions."""
    from app.config import get_settings
    from app.services.health_service import HealthService

    settings = get_settings()

    # Build connector_manager lazily (may fail if API keys are missing)
    connector_manager = None
    try:
        from app.connectors.manager import create_default_manager

        connector_manager = create_default_manager(
            openalex_email=settings.unpaywall_email,
            semantic_scholar_api_key=settings.semantic_scholar_api_key,
            searxng_url=settings.searxng_url,
            firecrawl_api_key=settings.firecrawl_api_key,
        )
    except Exception as exc:
        logger.debug("health_connector_manager_unavailable", error=str(exc))

    health_service = HealthService(
        db_session_factory=db_factory,
        redis_url=settings.redis_url,
        connector_manager=connector_manager,
    )

    try:
        overall = await health_service.check_all()
    except Exception as exc:
        logger.error("health_monitor_check_failed", error=str(exc))
        return

    # ── Log overall status ──────────────────────────────────────────
    if overall.status == "healthy":
        logger.info("health_monitor_check", status=overall.status)
    else:
        logger.warning(
            "health_monitor_check",
            status=overall.status,
            check_details={
                name: {"status": r.status, "error": r.error}
                for name, r in overall.checks.items()
            },
        )

    # ── Detect state transitions ────────────────────────────────────
    alerts: list[dict[str, Any]] = []
    for service_name, result in overall.checks.items():
        should_alert, previous_status = _should_alert(service_name, result.status)

        if should_alert:
            alert = {
                "service": service_name,
                "previous_status": previous_status,
                "current_status": result.status,
                "error": result.error,
                "details": result.details,
            }
            alerts.append(alert)

            logger.error(
                "health_service_degraded",
                service=service_name,
                previous=previous_status,
                current=result.status,
                error=result.error,
            )

        # Update cached state for next cycle
        _previous_check_results[service_name] = result.status

    # ── Send alert email if applicable ──────────────────────────────
    if alerts and settings.notification_email_enabled and settings.smtp_host:
        try:
            from app.services.notification_service import _send_smtp_sync

            ", ".join(a["service"] for a in alerts)
            subject = (
                f"[Autoscience Health] {overall.status.upper()}: "
                f"{len(alerts)} service(s) degraded"
            )
            body = _build_alert_body(overall, alerts)

            await asyncio.to_thread(
                _send_smtp_sync,
                to_email=settings.smtp_from,
                subject=subject,
                body=body,
            )
            logger.info(
                "health_alert_email_sent",
                services=[a["service"] for a in alerts],
            )
        except Exception as exc:
            logger.warning("health_alert_email_failed", error=str(exc))
