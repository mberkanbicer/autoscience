"""Smoke test for idle scheduler distributed lock."""

from unittest.mock import AsyncMock

import pytest

from app.services.idle_scheduler import _acquire_distributed_lock, _release_distributed_lock


@pytest.mark.asyncio
async def test_distributed_lock_acquire_and_release():
    redis = AsyncMock()
    redis.set = AsyncMock(return_value=True)
    redis.eval = AsyncMock(return_value=1)

    token = await _acquire_distributed_lock(redis)
    assert token is not None
    redis.set.assert_awaited_once()

    await _release_distributed_lock(redis, token)
    redis.eval.assert_awaited_once()