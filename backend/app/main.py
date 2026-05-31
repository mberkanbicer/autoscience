"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    print(f"Starting {settings.app_name} in {settings.app_env} mode")
    
    # Start idle cycle scheduler
    from .database import async_session_factory
    from .services.idle_scheduler import start_idle_scheduler
    await start_idle_scheduler(async_session_factory, interval_minutes=30)
    
    yield
    
    # Shutdown
    from .services.idle_scheduler import stop_idle_scheduler
    await stop_idle_scheduler()
    print(f"Shutting down {settings.app_name}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Background Scientific Cognition System",
        version="0.1.0",
        docs_url="/docs" if settings.app_debug else None,
        redoc_url="/redoc" if settings.app_debug else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "service": settings.app_name}

    # Import and include API router
    from .api.router import api_router

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
