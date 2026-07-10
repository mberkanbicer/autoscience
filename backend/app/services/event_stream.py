"""Redis Pub/Sub event broadcaster for live research preview."""

import asyncio
import json
from datetime import UTC, datetime, timezone
from typing import Any

import structlog
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

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

    async def publish(self, run_id: str, event_type: str, data: dict[str, Any] | None = None, event_id: str | None = None) -> None:
        """Publish an event to the run's channel.

        Event format:
        {
            "id": "uuid",
            "type": "keyword_expansion" | ...,
            "timestamp": "ISO8601",
            "data": { ... }
        }
        """
        event = {
            "id": event_id,
            "type": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "data": data or {},
        }
        channel = self._channel(run_id)
        try:
            await self.redis.publish(channel, json.dumps(event, default=str))
            logger.debug("event_published", run_id=run_id, event_type=event_type)
        except (RedisConnectionError, RedisTimeoutError, OSError) as e:
            logger.warning("event_publish_connection_error", error=str(e), run_id=run_id, event_type=event_type)
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
        except (RedisConnectionError, RedisTimeoutError, OSError) as e:
            logger.warning("subscribe_connection_error", error=str(e), run_id=run_id)
            return None
        except Exception as e:
            logger.warning("subscribe_failed", error=str(e), run_id=run_id)
            return None

    async def unsubscribe(self, pubsub) -> None:
        """Unsubscribe from a channel."""
        try:
            await pubsub.unsubscribe()
            await pubsub.close()
        except (RedisConnectionError, OSError):
            pass
        except Exception as exc:
            logger.debug("event_unsubscribe_cleanup_failed", error=str(exc), exc_info=True)
