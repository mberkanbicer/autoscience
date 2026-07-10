"""Redis-based cache service with TTL and force-refresh support."""

import hashlib
import json
from typing import Any

import structlog

logger = structlog.get_logger()


class CacheService:
    """Redis cache with configurable TTL and force-refresh bypass.

    Cache keys are SHA-256 hashes of the normalized inputs.
    On Redis failure, operates without cache (graceful degradation).
    """

    def __init__(self, redis_client, default_ttl_seconds: int = 3600, prefix: str = "cache"):
        self.redis = redis_client
        self.default_ttl = default_ttl_seconds
        self.prefix = prefix

    def _make_key(self, namespace: str, **kwargs) -> str:
        """Create a deterministic cache key from inputs."""
        # Sort keys for deterministic hashing
        raw = json.dumps(kwargs, sort_keys=True, default=str)
        h = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"{self.prefix}:{namespace}:{h}"

    async def get(
        self,
        namespace: str,
        force_refresh: bool = False,
        **kwargs,
    ) -> tuple[Any | None, bool]:
        """Get a cached value.

        Returns (value, hit) where hit indicates cache hit.
        If force_refresh is True, always returns (None, False).
        """
        if force_refresh:
            return None, False

        key = self._make_key(namespace, **kwargs)
        try:
            raw = await self.redis.get(key)
            if raw is not None:
                data = json.loads(raw)
                logger.debug("cache_hit", key=key, namespace=namespace)
                return data, True
        except json.JSONDecodeError as e:
            logger.warning("cache_get_parse_failed", error=str(e), key=key)
        except Exception as e:
            logger.warning("cache_get_failed", error=str(e), key=key)

        return None, False

    async def set(
        self,
        namespace: str,
        value: Any,
        ttl_seconds: int | None = None,
        **kwargs,
    ) -> None:
        """Store a value in cache with TTL."""
        key = self._make_key(namespace, **kwargs)
        ttl = ttl_seconds or self.default_ttl
        try:
            serialized = json.dumps(value, default=str)
            await self.redis.setex(key, ttl, serialized)
            logger.debug("cache_set", key=key, namespace=namespace, ttl=ttl)
        except (TypeError, ValueError) as e:
            logger.warning("cache_set_serialize_failed", error=str(e), key=key)
        except Exception as e:
            logger.warning("cache_set_failed", error=str(e), key=key)

    async def invalidate(self, namespace: str, **kwargs) -> bool:
        """Remove a specific cached entry."""
        key = self._make_key(namespace, **kwargs)
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.warning("cache_invalidate_failed", error=str(e), key=key)
            return False

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        try:
            await self.redis.info("keyspace")
            keys = await self.redis.keys(f"{self.prefix}:*")
            total_size = sum(
                await self.redis.memory_usage(k) or 0
                for k in keys[:100]  # Sample for performance
            )
            return {
                "total_entries": len(keys),
                "total_size_bytes": total_size,
                "total_size_kb": round(total_size / 1024, 1),
                "prefix": self.prefix,
            }
        except (AttributeError, TypeError) as e:
            logger.warning("cache_stats_missing_method", error=str(e))
            return {"total_entries": 0, "error": str(e)}
        except Exception as e:
            logger.warning("cache_stats_failed", error=str(e))
            return {"total_entries": 0, "error": str(e)}

    async def clear(self, namespace: str | None = None) -> int:
        """Clear cache entries. If namespace is given, only clear that namespace."""
        try:
            pattern = f"{self.prefix}:{namespace}:*" if namespace else f"{self.prefix}:*"
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning("cache_clear_failed", error=str(e))
            return 0
