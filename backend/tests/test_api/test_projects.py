"""Tests for project API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint.

    Notes:
        In test environments, external services (Redis, LLM providers,
        academic source connectors) are typically not configured or
        unavailable, so the overall status may be ``"degraded"`` or
        ``"unhealthy"``.  We accept all three statuses and verify that
        the endpoint structure is correct.
    """
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded", "unhealthy")
    assert data["version"] == "0.1.0"
    assert "checks" in data
    assert "database" in data["checks"]


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    """Test creating a project."""
    project_data = {
        "name": "Test Project",
        "domain": "AI research",
        "description": "A test project",
        "subject_scope": ["machine learning", "NLP"],
        "out_of_scope": ["consumer apps"],
        "default_flexibility": 0.7,
        "idle_research_enabled": True,
        "idle_trigger_minutes": 60,
        "max_idle_cycles_per_day": 5,
        "max_sources_per_cycle": 100,
        "approval_required_for_external_actions": True,
    }

    response = await client.post("/api/v1/projects", json=project_data)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Test Project"
    assert data["domain"] == "AI research"
    assert data["subject_scope"] == ["machine learning", "NLP"]
    assert data["default_flexibility"] == 0.7
    assert data["idle_research_enabled"] is True
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient):
    """Test listing projects."""
    # Create a project first
    project_data = {
        "name": "List Test Project",
        "domain": "Test domain",
    }
    await client.post("/api/v1/projects", json=project_data)

    # List projects
    response = await client.get("/api/v1/projects")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient):
    """Test getting a project by ID."""
    # Create a project
    project_data = {
        "name": "Get Test Project",
        "domain": "Test domain",
    }
    create_response = await client.post("/api/v1/projects", json=project_data)
    project_id = create_response.json()["id"]

    # Get the project
    response = await client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == "Get Test Project"


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    """Test getting a non-existent project."""
    response = await client.get("/api/v1/projects/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient):
    """Test updating a project."""
    # Create a project
    project_data = {
        "name": "Update Test Project",
        "domain": "Test domain",
    }
    create_response = await client.post("/api/v1/projects", json=project_data)
    project_id = create_response.json()["id"]

    # Update the project
    update_data = {
        "name": "Updated Project Name",
        "domain": "Updated domain",
    }
    response = await client.put(f"/api/v1/projects/{project_id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Updated Project Name"
    assert data["domain"] == "Updated domain"


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient):
    """Test deleting a project."""
    # Create a project
    project_data = {
        "name": "Delete Test Project",
        "domain": "Test domain",
    }
    create_response = await client.post("/api/v1/projects", json=project_data)
    project_id = create_response.json()["id"]

    # Delete the project
    response = await client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204

    # Verify it's deleted
    get_response = await client.get(f"/api/v1/projects/{project_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_project_stats(client: AsyncClient):
    """Test getting project statistics."""
    # Create a project
    project_data = {
        "name": "Stats Test Project",
        "domain": "Test domain",
    }
    create_response = await client.post("/api/v1/projects", json=project_data)
    project_id = create_response.json()["id"]

    # Get stats
    response = await client.get(f"/api/v1/projects/{project_id}/stats")
    assert response.status_code == 200

    data = response.json()
    assert "total_ideas" in data
    assert "active_ideas" in data
    assert "rejected_ideas" in data
    assert "total_runs" in data
    assert "total_papers" in data
    assert "total_skills" in data
    assert data["total_ideas"] == 0
    assert data["total_papers"] == 0
