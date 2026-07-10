"""Tests for v2.4 remaining backlog APIs."""

import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.models.report import AnalysisArtifact, AnalysisRun, KnowledgeNote
from app.models.research_run import ResearchRun


@pytest.mark.asyncio
async def test_skills_rbac_viewer_cannot_create(client: AsyncClient, sample_project):
    await client.post(
        "/api/v1/collaboration/members",
        json={
            "project_id": sample_project.id,
            "email": "owner@test.com",
            "display_name": "Owner",
            "role": "owner",
        },
        headers={"X-User-Email": "owner@test.com"},
    )
    await client.post(
        "/api/v1/collaboration/members",
        json={
            "project_id": sample_project.id,
            "email": "viewer@test.com",
            "display_name": "Viewer",
            "role": "viewer",
        },
        headers={"X-User-Email": "owner@test.com"},
    )

    response = await client.post(
        "/api/v1/skills",
        json={
            "name": "Forbidden Skill",
            "skill_type": "planning",
            "project_id": sample_project.id,
        },
        headers={"X-User-Email": "viewer@test.com"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_power_analysis_endpoint(client: AsyncClient, sample_project):
    response = await client.post(
        "/api/v1/sandbox/power-analysis",
        json={
            "project_id": sample_project.id,
            "test_type": "two_sample_ttest",
            "effect_size": 0.5,
        },
        headers={"X-User-Email": "analyst@test.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["test_type"] == "two_sample_ttest"
    assert data["sample_size_per_group"] > 0


@pytest.mark.asyncio
async def test_wiki_graph_endpoint(client: AsyncClient, sample_project, db_session):
    run_id = str(uuid4())
    db_session.add(
        ResearchRun(
            id=run_id,
            project_id=sample_project.id,
            run_type="user_directed",
            state="completed",
        )
    )
    note_a = KnowledgeNote(
        id=str(uuid4()),
        project_id=sample_project.id,
        run_id=run_id,
        note_type="hypothesis",
        entity_id="entity-1",
        title="Note A",
        content="Content A",
        linked_notes=[],
    )
    note_b = KnowledgeNote(
        id=str(uuid4()),
        project_id=sample_project.id,
        run_id=run_id,
        note_type="hypothesis",
        entity_id="entity-1",
        title="Note B",
        content="Content B",
        linked_notes=[note_a.id],
    )
    db_session.add_all([note_a, note_b])
    await db_session.commit()

    response = await client.get(
        f"/api/v1/wiki/graph?project_id={sample_project.id}",
    )
    assert response.status_code == 200
    graph = response.json()
    assert graph["stats"]["note_count"] == 2
    assert len(graph["edges"]) >= 1


@pytest.mark.asyncio
async def test_notebook_export_endpoint(
    client: AsyncClient, sample_project, db_session
):
    run_id = str(uuid4())
    db_session.add(
        ResearchRun(
            id=run_id,
            project_id=sample_project.id,
            run_type="user_directed",
            state="completed",
        )
    )
    analysis_id = str(uuid4())
    db_session.add(
        AnalysisRun(
            id=analysis_id,
            run_id=run_id,
            script="print('sandbox')",
            status="completed",
        )
    )
    db_session.add(
        AnalysisArtifact(
            id=str(uuid4()),
            analysis_run_id=analysis_id,
            artifact_type="stdout",
            file_path="/tmp/out.txt",
            description="stdout capture",
        )
    )
    await db_session.commit()

    response = await client.get(f"/api/v1/runs/{run_id}/notebook")
    assert response.status_code == 200
    notebook = response.json()
    assert notebook["nbformat"] == 4
    assert "sandbox" in str(notebook["cells"])


@pytest.mark.asyncio
async def test_review_notifications(client: AsyncClient, sample_project):
    owner_headers = {"X-User-Email": "owner@test.com", "X-User-Name": "Owner"}
    assignee_headers = {"X-User-Email": "assignee@test.com", "X-User-Name": "Assignee"}

    await client.post(
        "/api/v1/collaboration/members",
        json={
            "project_id": sample_project.id,
            "email": "owner@test.com",
            "display_name": "Owner",
            "role": "owner",
        },
        headers=owner_headers,
    )
    assignee_member = await client.post(
        "/api/v1/collaboration/members",
        json={
            "project_id": sample_project.id,
            "email": "assignee@test.com",
            "display_name": "Assignee",
            "role": "editor",
        },
        headers=owner_headers,
    )
    assignee_id = assignee_member.json()["user_id"]

    await client.post(
        "/api/v1/collaboration/reviews",
        json={
            "project_id": sample_project.id,
            "title": "Review paper draft",
            "entity_type": "paper",
            "assignee_id": assignee_id,
        },
        headers=owner_headers,
    )

    response = await client.get(
        f"/api/v1/collaboration/notifications?project_id={sample_project.id}",
        headers=assignee_headers,
    )
    assert response.status_code == 200
    notifications = response.json()
    assert len(notifications) == 1
    assert notifications[0]["title"] == "Review paper draft"


@pytest.mark.asyncio
async def test_oauth_providers_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/auth/oauth/providers")
    assert response.status_code == 200
    assert "providers" in response.json()