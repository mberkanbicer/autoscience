"""Tests for idle cycle persistence."""

from uuid import uuid4

import pytest

from app.engine.idle_cognition import IdleCycleResult
from app.models.project import Project
from app.services.idle_cycle_service import IdleCycleService


@pytest.mark.asyncio
async def test_store_and_list_idle_cycles(db_session):
    project_id = str(uuid4())
    db_session.add(
        Project(
            id=project_id,
            name="Idle Test",
            domain="ML",
            default_flexibility=0.6,
            idle_research_enabled=True,
            idle_trigger_minutes=120,
            max_idle_cycles_per_day=3,
            max_sources_per_cycle=50,
            approval_required_for_external_actions=True,
        )
    )
    await db_session.flush()

    service = IdleCycleService(db_session)
    result = IdleCycleResult(
        cycle_id=str(uuid4()),
        idle_mode="frontier_scan",
        ideas_generated=2,
        questions_generated=1,
        duration_seconds=12.5,
        cost_usd=0.4,
    )

    stored = await service.store_cycle(project_id, result)
    cycles = await service.get_project_cycles(project_id)
    stats = await service.get_cycle_statistics(project_id)

    assert stored.project_id == project_id
    assert len(cycles) == 1
    assert stats["total_cycles"] == 1
    assert stats["total_ideas"] == 2