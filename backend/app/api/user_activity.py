"""User activity tracking for idle trigger detection."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.services.user_activity_service import record_user_activity

router = APIRouter()


@router.post("")
async def track_user_activity(
    project_id: Annotated[str, Query()],
) -> dict:
    """Track that a user interacted with a project.

    Called from the frontend when users visit pages or take actions.
    Prevents the idle scheduler from starting cycles for active projects.
    """
    await record_user_activity(project_id)
    return {"status": "recorded", "project_id": project_id}
