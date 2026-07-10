"""Tests for durable user activity tracking."""

import pytest

from app.services import user_activity_service as activity


@pytest.mark.asyncio
async def test_record_and_read_activity_from_memory():
    project_id = "proj-activity-test"
    await activity.record_user_activity(project_id)

    last = await activity.get_last_activity(project_id)
    assert last is not None
    assert project_id in activity.get_tracked_project_ids()