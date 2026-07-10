"""Rate limiting middleware for API endpoints."""

import time

import structlog
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()

# Rate limit configuration
_rate_limit_config: dict[str, dict[str, int]] = {
    "default": {"limit": 100, "window": 60},
    "/runs": {"limit": 10, "window": 60},
    "/research/idle": {"limit": 5, "window": 60},
}


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_rate_limit_for_path(path: str) -> dict[str, int]:
    """Get rate limit config for a path."""
    # Try exact match first
    for prefix, config in _rate_limit_config.items():
        if prefix != "default" and path.startswith(prefix):
            return config
    return _rate_limit_config["default"]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits on API endpoints using Redis."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        config = _get_rate_limit_for_path(request.url.path)
        limit = config["limit"]
        window = config["window"]

        client_ip = _get_client_ip(request)
        key = f"rate_limit:{client_ip}:{request.url.path}"
        now = int(time.time())
        window_start = now - window

        try:
            from redis.asyncio import Redis

            from app.config import get_settings

            redis_client = Redis.from_url(get_settings().redis_url, decode_responses=True)
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, window)
            results = await pipe.execute()
            request_count = results[1]

            if request_count >= limit:
                logger.warning("rate_limit_exceeded", client_ip=client_ip, path=request.url.path)
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Maximum {limit} requests per {window} seconds.",
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, limit - request_count - 1))
            return response

        except Exception as e:
            logger.warning("rate_limit_redis_failed", error=str(e))
            return await call_next(request)
