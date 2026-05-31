"""Redis Pub/Sub event broadcaster for live research preview."""

import json
import asyncio
from typing import Any
from datetime import datetime

import structlog

logger = structlog.get_logger()


class EventBroadcaster:
    """Publishes workflow events to Redis Pub/Sub for SSE streaming.

    Each research run gets its own Redis channel: run:{run_id}:events
    Frontend subscribes via SSE to receive real-time updates.
    """

    CHANNEL_PREFIX = "run"

    def __init__(self, redis_client):
        self.redis = redis_client

    def _channel(self, run_id: str) -> str:
        return f"{self.CHANNEL_PREFIX}:{run_id}:events"

    async def publish(self, run_id: str, event_type: str, data: dict[str, Any] | None = None) -> None:
        """Publish an event to the run's channel.

        Event format:
        {
            "type": "keyword_expansion" | "search_started" | "search_results" | "paper_found" | ...,
            "timestamp": "ISO8601",
            "data": { ... }
        }
        """
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {},
        }
        channel = self._channel(run_id)
        try:
            await self.redis.publish(channel, json.dumps(event, default=str))
            logger.debug("event_published", run_id=run_id, event_type=event_type)
        except Exception as e:
            logger.warning("event_publish_failed", error=str(e), run_id=run_id, event_type=event_type)

    async def subscribe(self, run_id: str) -> asyncio.Queue | None:
        """Subscribe to a run's event channel.

        Returns an asyncio.Queue that receives events.
        Caller should consume from the queue and call unsubscribe when done.
        """
        channel = self._channel(run_id)
        pubsub = self.redis.pubsub()
        try:
            await pubsub.subscribe(channel)
            return pubsub
        except Exception as e:
            logger.warning("subscribe_failed", error=str(e), run_id=run_id)
            return None

    async def unsubscribe(self, pubsub) -> None:
        """Unsubscribe from a channel."""
        try:
            await pubsub.unsubscribe()
            await pubsub.close()
        except Exception:
            pass
