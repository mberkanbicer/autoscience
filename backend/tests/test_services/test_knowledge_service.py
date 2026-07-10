"""Tests for knowledge base wiki note upsert."""

from uuid import uuid4

import pytest

from app.models.project import Project
from app.models.research_run import ResearchRun
from app.services.knowledge_service import KnowledgeBaseService


@pytest.mark.asyncio
async def test_upsert_note_updates_existing_entity(db_session):
    project_id = str(uuid4())
    run_a = str(uuid4())
    run_b = str(uuid4())

    db_session.add(
        Project(
            id=project_id,
            name="Wiki Test",
            domain="ML",
            default_flexibility=0.6,
            idle_research_enabled=False,
            idle_trigger_minutes=120,
            max_idle_cycles_per_day=3,
            max_sources_per_cycle=50,
            approval_required_for_external_actions=True,
        )
    )
    db_session.add(
        ResearchRun(
            id=run_a,
            project_id=project_id,
            run_type="user_directed",
            state="completed",
        )
    )
    db_session.add(
        ResearchRun(
            id=run_b,
            project_id=project_id,
            run_type="user_directed",
            state="completed",
        )
    )
    await db_session.flush()

    service = KnowledgeBaseService(db_session)
    entity_id = str(uuid4())

    first = await service.upsert_note(
        project_id=project_id,
        note_type="paper",
        title="Paper: Alpha",
        content="Initial summary",
        entity_id=entity_id,
        run_id=run_a,
    )
    second = await service.upsert_note(
        project_id=project_id,
        note_type="paper",
        title="Paper: Alpha (updated)",
        content="Refined summary",
        entity_id=entity_id,
        run_id=run_b,
    )

    assert first.id == second.id
    assert second.title == "Paper: Alpha (updated)"
    assert second.content == "Refined summary"
    assert second.run_id == run_b