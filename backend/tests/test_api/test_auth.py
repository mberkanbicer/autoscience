"""Tests for JWT authentication."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_issue_token(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/token",
        json={"email": "alice@test.com", "display_name": "Alice"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["email"] == "alice@test.com"
    assert data["user"]["display_name"] == "Alice"


@pytest.mark.asyncio
async def test_auth_me_with_bearer(client: AsyncClient):
    token_response = await client.post(
        "/api/v1/auth/token",
        json={"email": "bob@test.com", "display_name": "Bob"},
    )
    token = token_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "bob@test.com"


@pytest.mark.asyncio
async def test_auth_me_rejects_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401