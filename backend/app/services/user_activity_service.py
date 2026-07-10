"""Durable user activity tracking for idle scheduler gating."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    import redis.asyncio as aioredis

logger = structlog.get_logger()

_activity_memory: dict[str, float] = {}
_redis_client: aioredis.Redis | None = None


def _activity_key(project_id: str) -> str:
    return f"activity:{project_id}"


async def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis.asyncio as aioredis

        from app.config import get_settings

        settings = get_settings()
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
        return _redis_client
    except (ImportError, ValueError, OSError) as exc:
        logger.debug("redis_unavailable_for_activity", error=str(exc))
        return None
    except Exception as exc:
        logger.warning("redis_unavailable_unexpected", error=str(exc))
        return None


async def record_user_activity(project_id: str, *, ttl_seconds: int = 86400) -> None:
    """Record user activity for a project (Redis with in-memory fallback)."""
    timestamp = time.time()
    _activity_memory[project_id] = timestamp

    redis_client = await _get_redis()
    if not redis_client:
        return

    try:
        await redis_client.set(_activity_key(project_id), str(timestamp), ex=ttl_seconds)
    except (ConnectionError, OSError, ValueError) as exc:
        logger.warning("activity_redis_write_connection_error", project_id=project_id, error=str(exc))
    except Exception as exc:
        logger.warning("activity_redis_write_failed", project_id=project_id, error=str(exc))


async def get_last_activity(project_id: str) -> float | None:
    """Return the last activity timestamp for a project, if known."""
    redis_client = await _get_redis()
    if redis_client:
        try:
            value = await redis_client.get(_activity_key(project_id))
            if value is not None:
                return float(value)
        except (ConnectionError, OSError, ValueError) as exc:
            logger.warning("activity_redis_read_connection_error", project_id=project_id, error=str(exc))
        except Exception as exc:
            logger.warning("activity_redis_read_failed", project_id=project_id, error=str(exc))

    return _activity_memory.get(project_id)


def get_tracked_project_ids() -> list[str]:
    """Return project IDs with in-memory activity records (debug/status)."""
    return list(_activity_memory.keys())
