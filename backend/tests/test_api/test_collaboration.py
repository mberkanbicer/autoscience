"""Tests for collaboration API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_comment(client: AsyncClient, sample_project):
    response = await client.post(
        "/api/v1/collaboration/comments",
        json={
            "project_id": sample_project.id,
            "entity_type": "paper",
            "entity_id": "paper-1",
            "body": "Needs stronger baseline comparison",
        },
        headers={"X-User-Email": "reviewer@test.com", "X-User-Name": "Reviewer"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["body"] == "Needs stronger baseline comparison"
    assert data["author_name"] == "Reviewer"


@pytest.mark.asyncio
async def test_first_member_becomes_owner(client: AsyncClient, sample_project):
    response = await client.post(
        "/api/v1/collaboration/members",
        json={
            "project_id": sample_project.id,
            "email": "owner@test.com",
            "display_name": "Owner",
            "role": "editor",
        },
        headers={"X-User-Email": "owner@test.com", "X-User-Name": "Owner"},
    )
    assert response.status_code == 201
    assert response.json()["role"] == "owner"