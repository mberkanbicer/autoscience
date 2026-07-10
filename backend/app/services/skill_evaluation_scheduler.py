"""Background scheduler for periodic skill performance evaluation.

Runs SkillPerformanceService.evaluate_all_skills() on a configurable interval
(every N hours) and logs results via AuditService.

Uses the same asyncio background-task pattern as the idle scheduler
(idle_scheduler.py) for consistency.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger()

_scheduler_task: asyncio.Task | None = None
_last_run_at: datetime | None = None
_last_run_result: dict[str, Any] | None = None
_run_count: int = 0

# Runtime configuration — stored at module level so it can be
# updated via the API and the scheduler will pick up changes
# on the next restart.
_runtime_config: dict[str, Any] = {
    "enabled": True,
    "interval_hours": 24,
    "dry_run": False,
}

# Stash the original factory and redis client so the scheduler can be
# restarted at runtime with the latest config
_db_factory = None
_redis_client = None

# System-wide event channel for SSE broadcasts
SYSTEM_EVAL_CHANNEL = "run:__system_skill_eval:events"


def get_scheduler_config() -> dict[str, Any]:
    """Get the current runtime scheduler configuration."""
    return dict(_runtime_config)


async def update_scheduler_config(
    db_factory,
    *,
    enabled: bool | None = None,
    interval_hours: int | None = None,
    dry_run: bool | None = None,
    redis_client=None,
) -> dict[str, Any]:
    """Update scheduler runtime config and restart if running.

    Apply changes to the module-level config, then stop and restart
    the scheduler loop so the new values take effect immediately.

    Args:
        db_factory: Async session factory (required if restarting).
        enabled: Whether the scheduler should run.
        interval_hours: How often to run evaluation.
        dry_run: When True, evaluates but never mutates skill statuses.
        redis_client: Optional Redis client for SSE broadcasting.

    Returns:
        The updated config dict.

    """
    if enabled is not None:
        _runtime_config["enabled"] = enabled
    if interval_hours is not None:
        _runtime_config["interval_hours"] = max(1, interval_hours)
    if dry_run is not None:
        _runtime_config["dry_run"] = dry_run

    # Stop current scheduler if running
    await stop_evaluation_scheduler()

    # Start new scheduler if enabled
    if _runtime_config["enabled"]:
        await start_evaluation_scheduler(
            db_factory=db_factory,
            interval_hours=_runtime_config["interval_hours"],
            dry_run=_runtime_config["dry_run"],
            redis_client=redis_client or _redis_client,
        )

    return dict(_runtime_config)


async def start_evaluation_scheduler(
    db_factory,
    interval_hours: int = 24,
    dry_run: bool = False,
    redis_client=None,
):
    """Start the background skill evaluation scheduler.

    Args:
        db_factory: Async session factory for creating DB sessions.
        interval_hours: How often to run evaluation (default 24).
        dry_run: When True, evaluates but never mutates skill statuses.
        redis_client: Optional Redis async client for broadcasting events
            via Pub/Sub to the SSE endpoint. When None, no broadcast occurs.

    """
    global _scheduler_task

    if _scheduler_task and not _scheduler_task.done():
        logger.info("eval_scheduler_already_running")
        return _scheduler_task

    # Stash references for potential runtime restart via update_scheduler_config
    global _db_factory, _redis_client
    _db_factory = db_factory
    _redis_client = redis_client
    _runtime_config["enabled"] = True
    _runtime_config["interval_hours"] = interval_hours
    _runtime_config["dry_run"] = dry_run

    async def _run_loop():
        logger.info(
            "eval_scheduler_started",
            interval_hours=interval_hours,
            dry_run=dry_run,
        )
        # Run once immediately on startup, then wait for the interval
        await _run_evaluation(db_factory, dry_run, redis_client)

        while True:
            await asyncio.sleep(interval_hours * 3600)
            try:
                await _run_evaluation(db_factory, dry_run, redis_client)
            except asyncio.CancelledError:
                raise
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error("eval_scheduler_cycle_error", error=str(e))

    _scheduler_task = asyncio.create_task(_run_loop())
    return _scheduler_task


async def stop_evaluation_scheduler():
    """Stop the background skill evaluation scheduler."""
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
        _scheduler_task = None
        logger.info("eval_scheduler_stopped")


async def _run_evaluation(db_factory, dry_run: bool, redis_client=None) -> None:
    """Run a single evaluation cycle across all projects."""
    global _last_run_at, _last_run_result, _run_count

    from sqlalchemy.exc import SQLAlchemyError

    from app.services.audit_service import AuditService
    from app.services.skill_performance_service import SkillPerformanceService

    logger.info("eval_scheduler_cycle_starting", dry_run=dry_run)

    evaluated_count = 0
    total_deprecated = 0
    total_retired = 0
    errors: list[str] = []
    summary = ""
    event_type = "skill_eval_completed"

    try:
        async with db_factory() as db:
            service = SkillPerformanceService(db)
            audit = AuditService(db)

            result = await service.evaluate_all_skills(
                project_id=None,  # All projects
                dry_run=dry_run,
            )

            evaluated_count = result.evaluated_count
            total_deprecated = len(result.deprecated)
            total_retired = len(result.retired)
            errors = result.errors
            summary = result.summary

            # Audit log the evaluation run
            await audit.log_event(
                event_type="skill_evaluation_scheduled",
                project_id=None,
                actor="system",
                action=(
                    f"Scheduled skill evaluation completed: "
                    f"{evaluated_count} evaluated, "
                    f"{total_deprecated} deprecated, "
                    f"{total_retired} retired"
                ),
                details={
                    "evaluated_count": evaluated_count,
                    "deprecated_count": total_deprecated,
                    "retired_count": total_retired,
                    "error_count": len(errors),
                    "dry_run": dry_run,
                    "summary": summary,
                },
            )

            await db.commit()

    except (TypeError, ValueError, SQLAlchemyError) as e:
        logger.error("eval_scheduler_cycle_db_error", error=str(e))
        errors.append(str(e))
        event_type = "skill_eval_error"
    except Exception as e:
        logger.error("eval_scheduler_cycle_failed", error=str(e))
        errors.append(str(e))
        event_type = "skill_eval_error"

    # Always update globals — even on failure — so the status endpoint
    # reflects the most recent attempt rather than showing stale data.
    _last_run_at = datetime.now(UTC)
    _last_run_result = {
        "evaluated_count": evaluated_count,
        "deprecated_count": total_deprecated,
        "retired_count": total_retired,
        "error_count": len(errors),
        "dry_run": dry_run,
        "errors": errors,
        "summary": summary,
    }
    _run_count += 1

    # Broadcast event via Redis Pub/Sub when Redis is available
    if redis_client is not None:
        try:
            from app.services.event_stream import EventBroadcaster
            broadcaster = EventBroadcaster(redis_client)
            await broadcaster.publish(
                run_id="__system_skill_eval",
                event_type=event_type,
                data={
                    "evaluated_count": evaluated_count,
                    "deprecated_count": total_deprecated,
                    "retired_count": total_retired,
                    "error_count": len(errors),
                    "dry_run": dry_run,
                    "summary": summary,
                    "run_number": _run_count,
                },
            )
        except (ConnectionError, OSError) as broadcast_err:
            logger.warning("eval_broadcast_connection_error", error=str(broadcast_err))
        except Exception as broadcast_err:
            logger.warning("eval_broadcast_failed", error=str(broadcast_err))

    if errors and not (total_deprecated or total_retired):
        logger.warning(
            "eval_scheduler_cycle_errors",
            error_count=len(errors),
        )
    elif total_deprecated > 0 or total_retired > 0:
        logger.info(
            "eval_scheduler_changes_made",
            deprecated=total_deprecated,
            retired=total_retired,
        )
    else:
        logger.info(
            "eval_scheduler_no_changes",
            evaluated=evaluated_count,
        )


def get_scheduler_status() -> dict[str, Any]:
    """Get the current evaluation scheduler status."""
    return {
        "running": _scheduler_task is not None and not _scheduler_task.done(),
        "run_count": _run_count,
        "last_run_at": _last_run_at.isoformat() if _last_run_at else None,
        "last_run_result": _last_run_result,
    }
