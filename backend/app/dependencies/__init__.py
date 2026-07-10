"""FastAPI dependency injection providers."""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import async_session_factory

logger = structlog.get_logger()

if TYPE_CHECKING:
    from app.connectors.manager import ConnectorManager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session for API dependency injection."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_connector_manager() -> "ConnectorManager":
    """Build connector manager with optional Redis-backed literature cache."""
    from app.connectors.manager import ConnectorManager, create_default_manager
    from app.services.cache_service import CacheService

    settings = get_settings()
    cache_service = None
    try:
        from app.utils.redis_client import create_async_redis_client

        redis_client = create_async_redis_client(decode_responses=True)
        cache_service = CacheService(
            redis_client,
            default_ttl_seconds=settings.cache_ttl_seconds,
            prefix="literature",
        )
    except Exception:
        logger.warning("redis_cache_init_failed", exc_info=True)
        cache_service = None

    return create_default_manager(
        openalex_email=settings.unpaywall_email,
        semantic_scholar_api_key=settings.semantic_scholar_api_key,
        searxng_url=settings.searxng_url,
        firecrawl_api_key=settings.firecrawl_api_key,
        cache_service=cache_service,
        cache_ttl_seconds=settings.cache_ttl_seconds,
    )
