"""Smoke test that key API routes are registered."""

import pytest
from httpx import AsyncClient


REQUIRED_PATHS = [
    "/api/v1/health",
    "/api/v1/auth/token",
    "/api/v1/auth/me",
    "/api/v1/auth/oauth/providers",
    "/api/v1/collaboration/reviews",
    "/api/v1/collaboration/activity",
    "/api/v1/collaboration/notifications",
    "/api/v1/papers/arxiv/search",
    "/api/v1/papers/resolve-doi",
    "/api/v1/papers/import-arxiv",
    "/api/v1/projects/domain-packs/list",
    "/api/v1/collaboration/reviews/{proposal_id}/simulate",
    "/api/v1/wiki/graph",
    "/api/v1/sandbox/power-analysis",
    "/api/v1/sandbox/plotly",
    "/api/v1/runs/{run_id}/notebook",
]


@pytest.mark.asyncio
async def test_openapi_includes_required_paths(client: AsyncClient):
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json().get("paths", {})
    missing = [path for path in REQUIRED_PATHS if path not in paths]
    assert not missing, f"Missing OpenAPI paths: {missing}"