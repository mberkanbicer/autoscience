"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import get_settings
from .middleware.auth import AuthMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.request_validation import RequestValidationMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    settings = get_settings()
    print(f"Starting {settings.app_name} in {settings.app_env} mode")

    # Start health monitor if enabled
    if settings.health_check_enabled:
        try:
            from .database import async_session_factory
            from .services.health_monitor import start_health_monitor
            await start_health_monitor(
                async_session_factory,
                interval_minutes=settings.health_check_interval_minutes,
            )
            print(f"Health monitor started (interval: {settings.health_check_interval_minutes} minutes)")
        except Exception as e:
            print(f"Warning: Failed to start health monitor: {e}")

    # Start idle scheduler if enabled
    if settings.idle_enabled:
        try:
            from .database import async_session_factory
            from .services.idle_scheduler import start_idle_scheduler
            await start_idle_scheduler(async_session_factory, settings.idle_check_interval_minutes)
            print(f"Idle scheduler started (interval: {settings.idle_check_interval_minutes} minutes)")
        except Exception as e:
            print(f"Warning: Failed to start idle scheduler: {e}")

    # Start skill evaluation scheduler if enabled
    if settings.skill_eval_enabled:
        try:
            from .database import async_session_factory
            from .services.skill_evaluation_scheduler import start_evaluation_scheduler

            # Create optional Redis client for event broadcasting
            eval_redis = None
            try:
                import redis.asyncio as aioredis
                eval_redis = aioredis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    socket_keepalive=True,
                    socket_timeout=5,
                )
            except Exception:
                pass

            await start_evaluation_scheduler(
                async_session_factory,
                interval_hours=settings.skill_eval_interval_hours,
                dry_run=settings.skill_eval_dry_run,
                redis_client=eval_redis,
            )
            print(
                f"Skill evaluation scheduler started "
                f"(interval: {settings.skill_eval_interval_hours}h, "
                f"dry_run: {settings.skill_eval_dry_run}, "
                f"broadcast: {eval_redis is not None})",
            )
        except Exception as e:
            print(f"Warning: Failed to start skill evaluation scheduler: {e}")

    yield

    # Shutdown
    print(f"Shutting down {settings.app_name}")
    try:
        from .services.health_monitor import stop_health_monitor
        await stop_health_monitor()
    except Exception as exc:
        logger.debug("health_monitor_stop_failed", error=str(exc))
    try:
        from .services.idle_scheduler import stop_idle_scheduler
        await stop_idle_scheduler()
    except Exception as exc:
        logger.debug("idle_scheduler_stop_failed", error=str(exc))
    try:
        from .services.skill_evaluation_scheduler import stop_evaluation_scheduler
        await stop_evaluation_scheduler()
    except Exception as exc:
        logger.debug("eval_scheduler_stop_failed", error=str(exc))


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="Background Scientific Cognition System",
        version="0.1.0",
        docs_url="/docs" if settings.app_debug else None,
        redoc_url="/redoc" if settings.app_debug else None,
        lifespan=lifespan,
    )

    # Request validation middleware (first)
    app.add_middleware(RequestValidationMiddleware)

    # Authentication middleware
    app.add_middleware(AuthMiddleware)

    # Rate limiting middleware
    app.add_middleware(RateLimitMiddleware)

    # CORS middleware
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import and include API router
    from .api.router import api_router

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
