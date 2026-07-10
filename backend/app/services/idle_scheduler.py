"""Background scheduler for idle cognition cycles."""

import asyncio
import time
from datetime import UTC, datetime, timezone

import structlog
from sqlalchemy import func, select

from app.models.project import Project
from app.models.research_run import IdleCycle, ResearchRun

from .user_activity_service import get_last_activity, get_tracked_project_ids

logger = structlog.get_logger()

_scheduler_task = None
_running_cycles: set[str] = set()  # project IDs currently running
_distributed_lock_key = "idle_scheduler_lock"
_lock_ttl_seconds = 60  # Lock TTL to prevent stale locks


async def _acquire_distributed_lock(redis_client) -> str | None:
    """Acquire distributed lock using Redis SETNX with TTL.

    Returns lock value if acquired, None otherwise.
    """
    try:
        import uuid
        lock_value = str(uuid.uuid4())
        acquired = await redis_client.set(
            _distributed_lock_key,
            lock_value,
            nx=True,  # Only set if key doesn't exist
            ex=_lock_ttl_seconds,  # Expire after TTL
        )
        if acquired:
            logger.info("distributed_lock_acquired")
        return lock_value if acquired else None
    except Exception as e:
        logger.warning("lock_acquire_failed", error=str(e))
        return None


async def _release_distributed_lock(redis_client, lock_value: str) -> None:
    """Release distributed lock only if owned by this process."""
    try:
        lua_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """
        await redis_client.eval(lua_script, 1, _distributed_lock_key, lock_value)
        logger.info("distributed_lock_released")
    except Exception as e:
        logger.warning("lock_release_failed", error=str(e))


async def start_idle_scheduler(db_factory, interval_minutes: int = 30):
    """Start the background idle cycle scheduler.
    
    Args:
        db_factory: Async session factory for creating DB sessions
        interval_minutes: How often to check for idle projects

    """
    global _scheduler_task

    if _scheduler_task and not _scheduler_task.done():
        logger.info("scheduler_already_running")
        return None

    async def _run_loop():
        logger.info("idle_scheduler_started", interval=interval_minutes)
        while True:
            try:
                await _check_and_run_idle_cycles(db_factory)
            except Exception as e:
                logger.error("idle_scheduler_error", error=str(e))
            await asyncio.sleep(interval_minutes * 60)

    _scheduler_task = asyncio.create_task(_run_loop())
    return _scheduler_task


async def stop_idle_scheduler():
    """Stop the background idle cycle scheduler."""
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
        _scheduler_task = None
        logger.info("idle_scheduler_stopped")


async def _check_and_run_idle_cycles(db_factory):
    """Check for projects that need idle cycles and run them with distributed locking."""
    from app.config import get_settings

    get_settings()

    # Try to acquire distributed lock to prevent race conditions across workers
    redis_client = None
    lock_value = None
    try:
        from app.utils.redis_client import create_async_redis_client

        redis_client = create_async_redis_client(decode_responses=True)
        lock_value = await _acquire_distributed_lock(redis_client)
        if not lock_value:
            logger.info("scheduler_lock_contended")
            return
    except Exception:
        # Without Redis, proceed without lock (single-worker fallback)
        pass


    try:
        async with db_factory() as db:
            # Find projects with idle research enabled
            result = await db.execute(
                select(Project).where(
                    Project.idle_research_enabled == True,  # noqa: E712
                ),
            )
            projects = list(result.scalars().all())

            for project in projects:
                # Skip if already running
                if project.id in _running_cycles:
                    continue

                # Check if there are active runs for this project
                active_result = await db.execute(
                    select(ResearchRun).where(
                        ResearchRun.project_id == project.id,
                        ResearchRun.state == "running",
                    ),
                )
                active_runs = list(active_result.scalars().all())
                if active_runs:
                    continue

                max_cycles = project.max_idle_cycles_per_day or 3
                today_start = datetime.now(UTC).replace(
                    hour=0, minute=0, second=0, microsecond=0,
                )
                cycles_today_result = await db.execute(
                    select(func.count(IdleCycle.id)).where(
                        IdleCycle.project_id == project.id,
                        IdleCycle.created_at >= today_start,
                    ),
                )
                cycles_today = cycles_today_result.scalar() or 0
                if cycles_today >= max_cycles:
                    logger.debug(
                        "idle_daily_limit_reached",
                        project_id=project.id,
                        cycles_today=cycles_today,
                        max_cycles=max_cycles,
                    )
                    continue

                last_activity = await get_last_activity(project.id)
                trigger_minutes = project.idle_trigger_minutes or 120

                if last_activity:
                    inactive_seconds = time.time() - last_activity
                    inactive_minutes = inactive_seconds / 60
                    if inactive_minutes < trigger_minutes:
                        logger.debug(
                            "project_still_active",
                            project_id=project.id,
                            inactive_minutes=round(inactive_minutes, 1),
                            trigger=trigger_minutes,
                        )
                        continue

                # Run idle cycle in background
                asyncio.create_task(_run_idle_for_project(project.id, db_factory))
                _running_cycles.add(project.id)
    finally:
        if redis_client and lock_value:
            await _release_distributed_lock(redis_client, lock_value)
        if redis_client:
            try:
                await redis_client.aclose()
            except Exception:
                pass


async def _run_idle_for_project(project_id: str, db_factory):
    """Run an idle cycle for a single project."""
    from app.config import get_settings
    from app.connectors.manager import create_default_manager
    from app.llm.router import create_default_router
    from app.services.orchestrator import ResearchOrchestrator

    settings = get_settings()

    try:
        # Build LLM router from env settings using the standard factory
        llm_router = create_default_router(
            openrouter_api_key=settings.openrouter_api_key,
            openrouter_default_model=settings.openrouter_default_model or "openai/gpt-4o",
            openrouter_base_url=settings.openrouter_base_url,
            openai_api_key=settings.openai_api_key,
            anthropic_api_key=settings.anthropic_api_key,
            local_base_url=settings.local_llm_base_url,
            local_model=settings.local_llm_model,
            llamacpp_base_url=settings.llamacpp_base_url,
            llamacpp_model=settings.llamacpp_model,
            default_provider=settings.default_llm_provider or "openrouter",
        )

        connector_manager = create_default_manager(
            openalex_email=settings.unpaywall_email,
            semantic_scholar_api_key=settings.semantic_scholar_api_key,
            searxng_url=settings.searxng_url,
            firecrawl_api_key=settings.firecrawl_api_key,
        )

        async with db_factory() as db:
            orchestrator = ResearchOrchestrator(
                db=db,
                llm_router=llm_router,
                connector_manager=connector_manager,
            )

            logger.info("idle_cycle_starting", project_id=project_id)
            result = await orchestrator.run_idle_cycle(project_id)

            logger.info(
                "idle_cycle_completed",
                project_id=project_id,
                ideas_generated=result.get("ideas_generated", 0),
                questions_generated=result.get("questions_generated", 0),
            )
    except Exception as e:
        logger.error("idle_cycle_failed", project_id=project_id, error=str(e))
    finally:
        _running_cycles.discard(project_id)


def get_scheduler_status() -> dict:
    """Get the current scheduler status."""
    return {
        "running": _scheduler_task is not None and not _scheduler_task.done(),
        "active_cycles": list(_running_cycles),
        "projects_with_activity": get_tracked_project_ids(),
    }
