"""Tests for notification service."""

import pytest

from app.services.notification_service import NotificationService


@pytest.mark.asyncio
async def test_email_skipped_when_smtp_disabled():
    service = NotificationService()
    sent = await service.send_review_assignment(
        assignee_email="user@test.com",
        assignee_name="User",
        proposal_title="Test Review",
        project_id="proj-1",
        proposal_id="prop-1",
        actor_name="Owner",
    )
    assert sent is False