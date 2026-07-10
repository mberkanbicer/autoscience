"""Unified Redis client factory with optional cluster support."""

from __future__ import annotations

from urllib.parse import urlparse

import redis.asyncio as aioredis

from app.config import get_settings


def _parse_cluster_nodes(raw: str) -> list[dict[str, str | int]]:
    nodes: list[dict[str, str | int]] = []
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if "://" in entry:
            parsed = urlparse(entry)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or 6379
        elif ":" in entry:
            host, port_str = entry.rsplit(":", 1)
            host = host.strip()
            port = int(port_str.strip())
        else:
            host = entry
            port = 6379
        nodes.append({"host": host, "port": port})
    return nodes


def create_async_redis_client(*, decode_responses: bool = True):
    """Create a standalone or cluster Redis client from settings."""
    settings = get_settings()
    if settings.redis_cluster_nodes.strip():
        from redis.asyncio.cluster import RedisCluster

        startup_nodes = _parse_cluster_nodes(settings.redis_cluster_nodes)
        return RedisCluster(
            startup_nodes=startup_nodes,
            decode_responses=decode_responses,
        )
    return aioredis.from_url(settings.redis_url, decode_responses=decode_responses)
