"""Tests for project RBAC enforcement."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_viewer_cannot_delete_project(client: AsyncClient):
    create_response = await client.post(
        "/api/v1/projects",
        json={"name": "RBAC Project", "domain": "testing"},
        headers={"X-User-Email": "owner@test.com", "X-User-Name": "Owner"},
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    await client.post(
        "/api/v1/collaboration/members",
        json={
            "project_id": project_id,
            "email": "viewer@test.com",
            "display_name": "Viewer",
            "role": "viewer",
        },
        headers={"X-User-Email": "owner@test.com", "X-User-Name": "Owner"},
    )

    delete_response = await client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"X-User-Email": "viewer@test.com", "X-User-Name": "Viewer"},
    )
    assert delete_response.status_code == 403


@pytest.mark.asyncio
async def test_owner_can_delete_project(client: AsyncClient):
    create_response = await client.post(
        "/api/v1/projects",
        json={"name": "Owner Delete", "domain": "testing"},
        headers={"X-User-Email": "owner2@test.com", "X-User-Name": "Owner"},
    )
    project_id = create_response.json()["id"]

    delete_response = await client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"X-User-Email": "owner2@test.com", "X-User-Name": "Owner"},
    )
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_viewer_cannot_create_idea(client: AsyncClient, sample_project):
    await client.post(
        "/api/v1/collaboration/members",
        json={
            "project_id": sample_project.id,
            "email": "owner@test.com",
            "display_name": "Owner",
            "role": "owner",
        },
        headers={"X-User-Email": "owner@test.com", "X-User-Name": "Owner"},
    )
    await client.post(
        "/api/v1/collaboration/members",
        json={
            "project_id": sample_project.id,
            "email": "viewer@test.com",
            "display_name": "Viewer",
            "role": "viewer",
        },
        headers={"X-User-Email": "owner@test.com", "X-User-Name": "Owner"},
    )

    response = await client.post(
        f"/api/v1/ideas?project_id={sample_project.id}",
        json={"text": "Forbidden idea"},
        headers={"X-User-Email": "viewer@test.com", "X-User-Name": "Viewer"},
    )
    assert response.status_code == 403