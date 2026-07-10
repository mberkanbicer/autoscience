"""Tests for domain specialization packs."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_domain_packs(client: AsyncClient):
    response = await client.get("/api/v1/projects/domain-packs/list")
    assert response.status_code == 200
    packs = response.json()
    assert len(packs) == 3
    ids = {pack["id"] for pack in packs}
    assert ids == {"physics", "biology", "chemistry"}


@pytest.mark.asyncio
async def test_apply_domain_pack(client: AsyncClient):
    create = await client.post(
        "/api/v1/projects",
        json={"name": "Pack Test", "domain": "general science"},
        headers={"X-User-Email": "owner@test.com", "X-User-Name": "Owner"},
    )
    project_id = create.json()["id"]

    response = await client.post(
        f"/api/v1/projects/{project_id}/apply-domain-pack?pack_id=biology",
        headers={"X-User-Email": "owner@test.com", "X-User-Name": "Owner"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "biology" in data["domain"].lower() or "Molecular" in data["domain"]
    assert "genomics" in data["subject_scope"]