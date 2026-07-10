"""Tests for unified SSE stream service."""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.sse_stream import (
    TERMINAL_EVENT_TYPES,
    format_sse_event,
    generate_run_events,
)


def test_format_sse_event():
    frame = format_sse_event("connected", {"run_id": "abc"}, event_id="evt-1")
    assert frame.startswith("data: ")
    payload = json.loads(frame.removeprefix("data: ").strip())
    assert payload["type"] == "connected"
    assert payload["id"] == "evt-1"
    assert payload["data"]["run_id"] == "abc"


@pytest.mark.asyncio
async def test_generate_run_events_replays_history_and_stops_for_terminal_run():
    run_id = str(uuid4())
    evt_id = str(uuid4())
    created_at = datetime.now(timezone.utc)

    class FakeEvent:
        def __init__(self):
            self.id = evt_id
            self.event_type = "run_completed"
            self.details = {"papers": 3}
            self.created_at = created_at

    class FakeRun:
        state = "completed"

    fake_event = FakeEvent()

    async def fake_replay(_run_id: str):
        return [format_sse_event("run_completed", {"papers": 3}, event_id=evt_id)], created_at, "completed"

    redis_client = AsyncMock()
    redis_client.close = AsyncMock()

    with patch("app.services.sse_stream._replay_history", new=AsyncMock(side_effect=fake_replay)):
        frames = []
        async for frame in generate_run_events(run_id, redis_client):
            frames.append(frame)

    assert len(frames) == 1
    payload = json.loads(frames[0].removeprefix("data: ").strip())
    assert payload["type"] == "run_completed"
    redis_client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_run_events_db_poll_fallback_when_redis_unavailable():
    run_id = str(uuid4())

    async def fake_replay(_run_id: str):
        return [], None, "running"

    redis_client = AsyncMock()
    redis_client.close = AsyncMock()

    with (
        patch("app.services.sse_stream._replay_history", new=AsyncMock(side_effect=fake_replay)),
        patch("app.services.sse_stream.EventBroadcaster.subscribe", new=AsyncMock(return_value=None)),
        patch("app.services.sse_stream._fetch_run_state", new=AsyncMock(return_value="completed")),
        patch("app.services.sse_stream._fetch_events_after", new=AsyncMock(return_value=[])),
    ):
        frames = []
        async for frame in generate_run_events(run_id, redis_client):
            frames.append(frame)

    assert any("connected" in frame for frame in frames)
    redis_client.close.assert_awaited_once()


def test_terminal_event_types_include_run_outcomes():
    assert "run_completed" in TERMINAL_EVENT_TYPES
    assert "run_failed" in TERMINAL_EVENT_TYPES