"""RBAC tests for reports API."""

import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.models.report import ResearchReport


@pytest.mark.asyncio
async def test_viewer_cannot_delete_report(client: AsyncClient, sample_project, db_session):
    owner_headers = {"X-User-Email": "owner@test.com", "X-User-Name": "Owner"}
    viewer_headers = {"X-User-Email": "viewer@test.com", "X-User-Name": "Viewer"}

    for email, name, role in [
        ("owner@test.com", "Owner", "owner"),
        ("viewer@test.com", "Viewer", "viewer"),
    ]:
        await client.post(
            "/api/v1/collaboration/members",
            json={
                "project_id": sample_project.id,
                "email": email,
                "display_name": name,
                "role": role,
            },
            headers=owner_headers,
        )

    report = ResearchReport(
        id=str(uuid4()),
        project_id=sample_project.id,
        title="Test Report",
        content_markdown="# Hello",
        report_type="summary",
    )
    db_session.add(report)
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/reports/{report.id}",
        headers=viewer_headers,
    )
    assert response.status_code == 403