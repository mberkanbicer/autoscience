"""Search API — SSE streaming + cached search endpoints."""

import json
import asyncio
from typing import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..config import get_settings
from ..services.cache_service import CacheService
from ..services.event_stream import EventBroadcaster
from ..connectors.searxng import SearXNGConnector
from ..connectors.base import SearchQuery

router = APIRouter()

settings = get_settings()


def _get_redis():
    """Get async Redis client."""
    return aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_keepalive=True,
        socket_timeout=None,
    )


def _get_cache_service(redis_client=None) -> CacheService:
    """Get cache service with Redis."""
    client = redis_client or _get_redis()
    return CacheService(client, default_ttl_seconds=settings.cache_ttl_seconds, prefix="search")


def _get_searxng_connector(cache_service: CacheService | None = None) -> SearXNGConnector:
    """Get SearXNG connector with optional caching."""
    return SearXNGConnector(
        base_url=settings.searxng_url,
        cache_service=cache_service,
        cache_ttl=settings.cache_ttl_seconds,
    )


@router.get("")
async def search(
    q: str = Query(..., description="Search query"),
    fresh: bool = Query(False, description="Bypass cache for fresh results"),
    categories: str = Query(None, description="Comma-separated SearXNG categories"),
    engines: str = Query(None, description="Comma-separated SearXNG engines"),
    limit: int = Query(20, ge=1, le=100),
    year_from: int | None = Query(None),
    year_to: int | None = Query(None),
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

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Search failed: {str(e)}")
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
async def clear_cache(namespace: str | None = Query(None)):
    """Clear search cache entries."""
    redis_client = _get_redis()
    cache = _get_cache_service(redis_client)
    try:
        cleared = await cache.clear(namespace)
        return {"cleared": cleared}
    finally:
        await redis_client.close()


async def _event_generator(run_id: str) -> AsyncGenerator[str, None]:
    """Generate SSE events from Redis Pub/Sub."""
    redis_client = _get_redis()
    broadcaster = EventBroadcaster(redis_client)
    pubsub = await broadcaster.subscribe(run_id)

    if not pubsub:
        yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'Failed to subscribe'}})}\n\n"
        await redis_client.close()
        return

    # Check if run is already completed/failed (events may have been already sent)
    from ..database import async_session_factory
    from ..services.research_run_service import ResearchRunService
    run_completed = False
    try:
        async with async_session_factory() as check_db:
            check_svc = ResearchRunService(check_db)
            run = await check_svc.get_run(run_id)
            if run and run.state in ("completed", "failed"):
                # Send stored events from DB
                from sqlalchemy import select
                from ..models.research_run import ResearchRunEvent
                stmt = select(ResearchRunEvent).where(
                    ResearchRunEvent.run_id == run_id
                ).order_by(ResearchRunEvent.created_at)
                result = await check_db.execute(stmt)
                for evt in result.scalars().all():
                    sse_data = {
                        "type": evt.event_type,
                        "timestamp": evt.created_at.isoformat() if evt.created_at else "",
                        "data": evt.details or {},
                    }
                    yield f"data: {json.dumps(sse_data, default=str)}\n\n"
                run_completed = True
    except Exception:
        pass

    if run_completed:
        await broadcaster.unsubscribe(pubsub)
        await redis_client.close()
        return

    # Send initial connection event
    yield f"data: {json.dumps({'type': 'connected', 'timestamp': __import__('datetime').datetime.utcnow().isoformat()})}\n\n"

    try:
        # Use listen() which blocks properly — not get_message() which polls
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                yield f"data: {data}\n\n"

                # Check if run completed
                try:
                    event = json.loads(data)
                    if event.get("type") in ("run_completed", "run_failed"):
                        break
                except json.JSONDecodeError:
                    pass

    except asyncio.CancelledError:
        pass
    except Exception as e:
        # Only send error event if connection is still alive
        try:
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(e)}})}\n\n"
        except Exception:
            pass
    finally:
        await broadcaster.unsubscribe(pubsub)
        await redis_client.close()


@router.get("/stream/{run_id}")
async def stream_run_events(run_id: str):
    """SSE endpoint for live research run events.

    Connect via EventSource:
        const es = new EventSource('/api/v1/search/stream/{run_id}');
        es.onmessage = (e) => {
            const event = JSON.parse(e.data);
            // event.type: "keywords" | "search_started" | "search_results" | "paper_found" | ...
            // event.data: { ... }
        };
    """
    return StreamingResponse(
        _event_generator(run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
