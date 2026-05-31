"""Background scheduler for idle cognition cycles."""

import asyncio
from datetime import datetime, timedelta

import structlog
from sqlalchemy import select

from ..models.project import Project

logger = structlog.get_logger()

_scheduler_task = None
_running_cycles: set[str] = set()  # project IDs currently running


async def start_idle_scheduler(db_factory, interval_minutes: int = 30):
    """Start the background idle cycle scheduler.
    
    Args:
        db_factory: Async session factory for creating DB sessions
        interval_minutes: How often to check for idle projects
    """
    global _scheduler_task
    
    if _scheduler_task and not _scheduler_task.done():
        logger.info("scheduler_already_running")
        return
    
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
    """Check for projects that need idle cycles and run them."""
    from ..services.orchestrator import ResearchOrchestrator
    from ..llm.router import LLMRouter
    from ..connectors.manager import create_default_manager
    from ..config import get_settings
    
    settings = get_settings()
    
    async with db_factory() as db:
        # Find projects with idle research enabled
        result = await db.execute(
            select(Project).where(
                Project.idle_research_enabled == True,  # noqa: E712
            )
        )
        projects = list(result.scalars().all())
        
        for project in projects:
            # Skip if already running
            if project.id in _running_cycles:
                continue
            
            # Check if enough time has passed since last idle cycle
            # Use a simple counter-based approach instead of last_idle_at
            if not hasattr(project, 'last_idle_at') or project.last_idle_at is None:
                # First run, allow it
                pass
            else:
                interval = (project.idle_interval_minutes or 60) * 60
                next_run = project.last_idle_at + timedelta(seconds=interval)
                if datetime.now() < next_run:
                    continue
            
            # Run idle cycle in background
            asyncio.create_task(_run_idle_for_project(project.id, db_factory))
            _running_cycles.add(project.id)


async def _run_idle_for_project(project_id: str, db_factory):
    """Run an idle cycle for a single project."""
    from ..services.orchestrator import ResearchOrchestrator
    from ..llm.router import LLMRouter
    from ..connectors.manager import create_default_manager
    from ..config import get_settings
    
    settings = get_settings()
    
    try:
        async with db_factory() as db:
            # Build LLM router from env settings
            llm_router = LLMRouter()
            if settings.openrouter_api_key:
                from ..llm.openrouter_provider import OpenRouterProvider
                llm_router.providers["openrouter"] = OpenRouterProvider(
                    api_key=settings.openrouter_api_key,
                    model=settings.openrouter_model or "openai/gpt-4o",
                )
                llm_router.default_provider = "openrouter"
            elif settings.openai_api_key:
                from ..llm.openai_provider import OpenAIProvider
                llm_router.providers["openai"] = OpenAIProvider(
                    api_key=settings.openai_api_key,
                    model=settings.openai_model or "gpt-4o",
                )
                llm_router.default_provider = "openai"
            
            connector_manager = create_default_manager()
            
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
    }
