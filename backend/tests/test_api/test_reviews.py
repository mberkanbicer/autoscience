"""Tests for review proposal workflow."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_update_review(client: AsyncClient, sample_project):
    headers = {"X-User-Email": "editor@test.com", "X-User-Name": "Editor"}

    create_response = await client.post(
        "/api/v1/collaboration/reviews",
        json={
            "project_id": sample_project.id,
            "title": "Review manuscript draft",
            "description": "Check methods section",
            "entity_type": "manuscript",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    proposal = create_response.json()
    assert proposal["status"] == "pending"
    assert proposal["created_by_name"] == "Editor"

    update_response = await client.patch(
        f"/api/v1/collaboration/reviews/{proposal['id']}",
        json={"status": "approved"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_list_reviews(client: AsyncClient, sample_project):
    headers = {"X-User-Email": "editor@test.com", "X-User-Name": "Editor"}
    await client.post(
        "/api/v1/collaboration/reviews",
        json={
            "project_id": sample_project.id,
            "title": "Peer review",
            "entity_type": "paper",
        },
        headers=headers,
    )

    list_response = await client.get(
        f"/api/v1/collaboration/reviews?project_id={sample_project.id}",
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1