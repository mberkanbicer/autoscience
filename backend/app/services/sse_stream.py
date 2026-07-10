"""Unified SSE event stream: DB replay, Redis live feed, DB poll fallback."""

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timezone
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import async_session_factory
from app.models.research_run import ResearchRun, ResearchRunEvent

from .event_stream import EventBroadcaster

logger = structlog.get_logger()

TERMINAL_RUN_STATES = frozenset({"completed", "failed", "cancelled"})
TERMINAL_EVENT_TYPES = frozenset({"run_completed", "run_failed"})
DB_POLL_INTERVAL_SECONDS = 1.5


def format_sse_event(
    event_type: str,
    data: dict[str, Any] | None = None,
    *,
    event_id: str | None = None,
    timestamp: str | None = None,
) -> str:
    """Serialize a single SSE data frame."""
    payload = {
        "id": event_id,
        "type": event_type,
        "timestamp": timestamp or datetime.now(UTC).isoformat(),
        "data": data or {},
    }
    return f"data: {json.dumps(payload, default=str)}\n\n"


def _event_to_sse(evt: ResearchRunEvent) -> str:
    return format_sse_event(
        evt.event_type,
        evt.details or {},
        event_id=evt.id,
        timestamp=evt.created_at.isoformat() if evt.created_at else None,
    )


async def _fetch_run_state(run_id: str) -> str:
    async with async_session_factory() as db:
        result = await db.execute(select(ResearchRun.state).where(ResearchRun.id == run_id))
        return result.scalar_one_or_none() or "created"


async def _fetch_events_after(
    run_id: str,
    *,
    after_created_at: datetime | None = None,
) -> list[ResearchRunEvent]:
    async with async_session_factory() as db:
        stmt = (
            select(ResearchRunEvent)
            .where(ResearchRunEvent.run_id == run_id)
            .order_by(ResearchRunEvent.created_at)
        )
        if after_created_at is not None:
            stmt = stmt.where(ResearchRunEvent.created_at > after_created_at)

        result = await db.execute(stmt)
        return list(result.scalars().all())


async def _replay_history(run_id: str) -> tuple[list[str], datetime | None, str]:
    """Replay persisted events and return frames plus cursor metadata."""
    frames: list[str] = []
    last_created_at: datetime | None = None
    run_state = "created"

    try:
        async with async_session_factory() as db:
            run_result = await db.execute(select(ResearchRun).where(ResearchRun.id == run_id))
            run = run_result.scalar_one_or_none()
            if run:
                run_state = run.state

            stmt = (
                select(ResearchRunEvent)
                .where(ResearchRunEvent.run_id == run_id)
                .order_by(ResearchRunEvent.created_at)
            )
            result = await db.execute(stmt)
            for evt in result.scalars().all():
                frames.append(_event_to_sse(evt))
                last_created_at = evt.created_at
    except SQLAlchemyError as e:
        logger.error("sse_history_fetch_failed", error=str(e), run_id=run_id)
    except Exception as e:
        logger.error("sse_history_fetch_unexpected", error=str(e), run_id=run_id)

    return frames, last_created_at, run_state


async def _yield_db_events(
    run_id: str,
    *,
    seen_event_ids: set[str],
    cursor_ts: datetime | None,
) -> AsyncGenerator[tuple[str, datetime | None, bool], None]:
    """Yield new DB events. Third value signals terminal event."""
    events = await _fetch_events_after(run_id, after_created_at=cursor_ts)
    for evt in events:
        if evt.id in seen_event_ids:
            continue
        seen_event_ids.add(evt.id)
        cursor_ts = evt.created_at
        terminal = evt.event_type in TERMINAL_EVENT_TYPES
        yield _event_to_sse(evt), cursor_ts, terminal
        if terminal:
            return


async def _live_loop(
    run_id: str,
    redis_client,
    *,
    seen_event_ids: set[str],
    cursor_ts: datetime | None,
    use_redis: bool,
    pubsub=None,
) -> AsyncGenerator[str, None]:
    """Stream live events via Redis with DB backfill, or DB-only when Redis is down."""
    broadcaster = EventBroadcaster(redis_client) if use_redis and pubsub else None

    try:
        while True:
            run_state = await _fetch_run_state(run_id)

            async for frame, new_cursor, terminal in _yield_db_events(
                run_id,
                seen_event_ids=seen_event_ids,
                cursor_ts=cursor_ts,
            ):
                cursor_ts = new_cursor
                yield frame
                if terminal:
                    return

            if run_state in TERMINAL_RUN_STATES:
                return

            if use_redis and pubsub:
                try:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=DB_POLL_INTERVAL_SECONDS,
                    )
                except asyncio.CancelledError:
                    raise
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning("redis_listen_parse_failed", error=str(e), run_id=run_id)
                    continue
                except Exception as e:
                    logger.warning("redis_listen_failed", error=str(e), run_id=run_id)
                    use_redis = False
                    pubsub = None
                    continue

                if message and message.get("type") == "message":
                    data = message.get("data")
                    if isinstance(data, bytes):
                        data = data.decode()
                    try:
                        event = json.loads(data)
                        event_id = event.get("id")
                        if event_id and event_id in seen_event_ids:
                            continue
                        if event_id:
                            seen_event_ids.add(event_id)
                        yield f"data: {json.dumps(event, default=str)}\n\n"
                        if event.get("type") in TERMINAL_EVENT_TYPES:
                            return
                    except json.JSONDecodeError:
                        yield f"data: {data}\n\n"
            else:
                await asyncio.sleep(DB_POLL_INTERVAL_SECONDS)
    finally:
        if broadcaster and pubsub:
            await broadcaster.unsubscribe(pubsub)


async def generate_run_events(
    run_id: str,
    redis_client,
) -> AsyncGenerator[str, None]:
    """Generate SSE frames for a research run."""
    seen_event_ids: set[str] = set()
    history_frames, cursor_ts, run_state = await _replay_history(run_id)

    for frame in history_frames:
        yield frame
        try:
            payload = json.loads(frame.removeprefix("data: ").strip())
            if payload.get("id"):
                seen_event_ids.add(payload["id"])
        except (json.JSONDecodeError, AttributeError):
            pass

    if run_state in TERMINAL_RUN_STATES:
        await redis_client.close()
        return

    if not history_frames:
        yield format_sse_event("connected")

    broadcaster = EventBroadcaster(redis_client)
    pubsub = await broadcaster.subscribe(run_id)
    use_redis = pubsub is not None
    if not use_redis:
        logger.warning("sse_redis_unavailable", run_id=run_id, fallback="db_poll")

    try:
        async for frame in _live_loop(
            run_id,
            redis_client,
            seen_event_ids=seen_event_ids,
            cursor_ts=cursor_ts,
            use_redis=use_redis,
            pubsub=pubsub,
        ):
            yield frame
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.warning("sse_stream_error", run_id=run_id, error=str(e))
        yield format_sse_event("error", {"message": str(e)})
    finally:
        if pubsub:
            await broadcaster.unsubscribe(pubsub)
        try:
            await redis_client.close()
        except (AttributeError, TypeError):
            pass
