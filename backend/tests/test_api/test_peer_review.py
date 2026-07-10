"""Tests for simulated peer review."""

import os

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.skipif(
    not any([
        os.environ.get("OPENAI_API_KEY"),
        os.environ.get("ANTHROPIC_API_KEY"),
        os.environ.get("OPENROUTER_API_KEY"),
    ]),
    reason="No LLM provider configured",
)
async def test_simulate_review_proposal(client: AsyncClient, sample_project):
    headers = {"X-User-Email": "editor@test.com", "X-User-Name": "Editor"}

    create = await client.post(
        "/api/v1/collaboration/reviews",
        json={
            "project_id": sample_project.id,
            "title": "Review draft methods",
            "description": "Check reproducibility",
            "entity_type": "manuscript",
        },
        headers=headers,
    )
    proposal_id = create.json()["id"]

    response = await client.post(
        f"/api/v1/collaboration/reviews/{proposal_id}/simulate",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]
    assert data["recommendation"] in {
        "accept",
        "minor_revision",
        "major_revision",
        "reject",
    }
    assert data["simulated"] is True

    updated = await client.get(
        f"/api/v1/collaboration/reviews?project_id={sample_project.id}",
    )
    assert updated.json()[0]["status"] == "in_review"