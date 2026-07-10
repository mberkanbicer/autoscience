"""Search API — SSE streaming + cached search endpoints."""

from collections.abc import AsyncGenerator
from typing import Annotated

import httpx
import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response, StreamingResponse

from app.config import get_settings
from app.connectors.base import SearchQuery
from app.connectors.searxng import SearXNGConnector
from app.services.cache_service import CacheService

logger = structlog.get_logger()

router = APIRouter()

# CORS headers for SSE — echo a configured origin (never "*" with credentials)
_ALLOWED_ORIGIN = (get_settings().cors_origins or ["http://localhost:3000"])[0]

SSE_CORS_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Access-Control-Allow-Origin": _ALLOWED_ORIGIN,
    "Access-Control-Allow-Credentials": "true",
}


def _cors_response(content=None, media_type="text/event-stream"):
    """Create response with CORS headers."""
    response = Response(content=content, media_type=media_type)
    for key, value in SSE_CORS_HEADERS.items():
        response.headers[key] = value
    return response


def _get_redis():
    """Get async Redis client."""
    settings = get_settings()
    return aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_keepalive=True,
        socket_timeout=None,
    )


def _get_cache_service(redis_client=None) -> CacheService:
    """Get cache service with Redis."""
    client = redis_client or _get_redis()
    settings = get_settings()
    return CacheService(client, default_ttl_seconds=settings.cache_ttl_seconds, prefix="search")


def _get_searxng_connector(cache_service: CacheService | None = None) -> SearXNGConnector:
    """Get SearXNG connector with optional caching."""
    settings = get_settings()
    return SearXNGConnector(
        base_url=settings.searxng_url,
        cache_service=cache_service,
        cache_ttl=settings.cache_ttl_seconds,
    )


@router.get("")
async def search(
    q: Annotated[str, Query(description="Search query")],
    fresh: Annotated[bool, Query(description="Bypass cache for fresh results")] = False,
    categories: Annotated[str, Query(description="Comma-separated SearXNG categories")] = None,
    engines: Annotated[str, Query(description="Comma-separated SearXNG engines")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    year_from: Annotated[int | None, Query()] = None,
    year_to: Annotated[int | None, Query()] = None,
):
    """Search via SearXNG with caching.

    Returns cached results by default. Set fresh=true to bypass cache.

    Response headers:
    - X-Cache: HIT or MISS
    - X-Cache-Age: seconds since cached (if HIT)
    """
    redis_client = _get_redis()
    cache = _get_cache_service(redis_client)
    connector = _get_searxng_connector(cache)

    cats = categories.split(",") if categories else None
    engs = engines.split(",") if engines else None

    query = SearchQuery(
        text=q,
        year_from=year_from,
        year_to=year_to,
        limit=limit,
    )

    try:
        result = await connector.search(
            query,
            force_refresh=fresh,
            categories=cats,
            engines=engs,
        )

        # Build response
        papers = [
            {
                "title": p.title,
                "authors": p.authors,
                "year": p.year,
                "doi": p.doi,
                "url": p.url,
                "abstract": (p.abstract or "")[:200],
                "source": p.source,
                "engine": p.raw_metadata.get("engine", ""),
                "score": p.raw_metadata.get("score", 0),
            }
            for p in result.papers
        ]

        response_data = {
            "query": q,
            "total_results": result.total_results,
            "papers": papers,
            "cached": not fresh,
        }

        # Determine cache status from headers
        cache_status = "MISS" if fresh else "HIT"

        from starlette.responses import JSONResponse
        response = JSONResponse(content=response_data)
        response.headers["X-Cache"] = cache_status
        return response

    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Search network error: {e!s}")
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=502, detail=f"Search response error: {e!s}")
    except Exception as e:
        logger.error("search_unexpected", error=str(e))
        raise HTTPException(status_code=502, detail="Search failed")
    finally:
        await redis_client.close()


@router.get("/cache/stats")
async def cache_stats():
    """Get search cache statistics."""
    redis_client = _get_redis()
    cache = _get_cache_service(redis_client)
    try:
        stats = await cache.get_stats()
        return stats
    finally:
        await redis_client.close()


@router.delete("/cache")
async def clear_cache(namespace: Annotated[str | None, Query()] = None):
    """Clear search cache entries."""
    redis_client = _get_redis()
    cache = _get_cache_service(redis_client)
    try:
        cleared = await cache.clear(namespace)
        return {"cleared": cleared}
    finally:
        await redis_client.close()


async def _event_generator(run_id: str) -> AsyncGenerator[str, None]:
    """Generate SSE events from DB replay, Redis live feed, and DB poll fallback."""
    from app.services.sse_stream import generate_run_events

    redis_client = _get_redis()
    async for frame in generate_run_events(run_id, redis_client):
        yield frame


@router.options("/stream/{run_id}")
async def stream_options(run_id: str):
    """Handle CORS preflight."""
    return _cors_response()


@router.get("/stream/{run_id}")
async def stream_run_events(run_id: str):
    """SSE endpoint for live research run events."""
    return StreamingResponse(
        _event_generator(run_id),
        media_type="text/event-stream",
        headers=SSE_CORS_HEADERS,
    )
