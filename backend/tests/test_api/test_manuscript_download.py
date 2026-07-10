"""Integration tests for manuscript download endpoints, including DOCX export."""

import pytest
from unittest.mock import patch
from uuid import uuid4

from httpx import AsyncClient


@pytest.mark.asyncio
async def test_manuscript_download_tex(client: AsyncClient):
    """Download manuscript as LaTeX (.tex) — the basic format."""
    project_resp = await client.post("/api/v1/projects", json={
        "name": "Manuscript Test",
        "domain": "Test",
    })
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    # Create a manuscript
    ms_resp = await client.post("/api/v1/manuscripts", json={
        "project_id": project_id,
        "title": "Test Manuscript",
        "run_id": None,
    })
    assert ms_resp.status_code == 200
    ms_id = ms_resp.json()["id"]

    # Download as .tex
    resp = await client.get(f"/api/v1/manuscripts/{ms_id}/download?format=tex")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    assert ".tex" in resp.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_manuscript_download_bib(client: AsyncClient):
    """Download manuscript bibliography as BibTeX."""
    project_resp = await client.post("/api/v1/projects", json={
        "name": "Manuscript Bib Test",
        "domain": "Test",
    })
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    ms_resp = await client.post("/api/v1/manuscripts", json={
        "project_id": project_id,
        "title": "BibTeX Test",
        "run_id": None,
    })
    assert ms_resp.status_code == 200
    ms_id = ms_resp.json()["id"]

    resp = await client.get(f"/api/v1/manuscripts/{ms_id}/download?format=bib")
    assert resp.status_code == 200
    assert ".bib" in resp.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_manuscript_download_zip(client: AsyncClient):
    """Download manuscript as .zip bundle (main.tex + references.bib)."""
    project_resp = await client.post("/api/v1/projects", json={
        "name": "Manuscript Zip Test",
        "domain": "Test",
    })
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    ms_resp = await client.post("/api/v1/manuscripts", json={
        "project_id": project_id,
        "title": "Zip Test",
        "run_id": None,
    })
    assert ms_resp.status_code == 200
    ms_id = ms_resp.json()["id"]

    resp = await client.get(f"/api/v1/manuscripts/{ms_id}/download?format=zip")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    assert ".zip" in resp.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_manuscript_download_docx_when_pandoc_available(client: AsyncClient):
    """DOCX export returns 200 when pandoc is installed on the server."""
    import shutil
    if not shutil.which("pandoc"):
        pytest.skip("pandoc not installed on this server")

    project_resp = await client.post("/api/v1/projects", json={
        "name": "DOCX Test",
        "domain": "Test",
    })
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    # Create manuscript with actual LaTeX content so pandoc has something to convert
    ms_resp = await client.post("/api/v1/manuscripts", json={
        "project_id": project_id,
        "title": "DOCX Export Test",
        "run_id": None,
    })
    assert ms_resp.status_code == 200
    ms_id = ms_resp.json()["id"]

    # Add LaTeX content
    update_resp = await client.patch(
        f"/api/v1/manuscripts/{ms_id}",
        json={"content_latex": (
            "\\documentclass{article}\\n"
            "\\begin{document}\\n"
            "\\section{Introduction}\\n"
            "This is a test manuscript for DOCX export.\\n"
            "\\end{document}"
        )},
    )
    assert update_resp.status_code == 200

    # Download as DOCX — should work since pandoc is available
    resp = await client.get(f"/api/v1/manuscripts/{ms_id}/download?format=docx")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert ".docx" in resp.headers.get("content-disposition", "")
    # Verify we got actual binary content (DOCX is a zip archive)
    content = resp.content
    assert len(content) > 100, "DOCX file should be larger than 100 bytes"
    assert content[:2] == b"PK", "DOCX should be a valid ZIP archive (starts with PK)"


@pytest.mark.asyncio
async def test_manuscript_download_docx_fallback_when_pandoc_missing(client: AsyncClient):
    """DOCX export returns 501 when pandoc is not available."""
    project_resp = await client.post("/api/v1/projects", json={
        "name": "DOCX Fallback Test",
        "domain": "Test",
    })
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    ms_resp = await client.post("/api/v1/manuscripts", json={
        "project_id": project_id,
        "title": "Fallback Test",
        "run_id": None,
    })
    assert ms_resp.status_code == 200
    ms_id = ms_resp.json()["id"]

    # Mock shutil.which to return None, simulating missing pandoc
    with patch("app.services.manuscript_service.shutil.which", return_value=None):
        resp = await client.get(f"/api/v1/manuscripts/{ms_id}/download?format=docx")

    assert resp.status_code == 501
    detail = resp.json().get("detail", "")
    assert "pandoc" in detail.lower()


@pytest.mark.asyncio
async def test_manuscript_download_invalid_format(client: AsyncClient):
    """Download with invalid format returns 422."""
    project_resp = await client.post("/api/v1/projects", json={
        "name": "Invalid Format Test",
        "domain": "Test",
    })
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    ms_resp = await client.post("/api/v1/manuscripts", json={
        "project_id": project_id,
        "title": "Invalid Format",
        "run_id": None,
    })
    assert ms_resp.status_code == 200
    ms_id = ms_resp.json()["id"]

    resp = await client.get(f"/api/v1/manuscripts/{ms_id}/download?format=invalid")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_manuscript_download_not_found(client: AsyncClient):
    """Download a non-existent manuscript returns 404."""
    resp = await client.get(
        f"/api/v1/manuscripts/{str(uuid4())}/download?format=tex"
    )
    assert resp.status_code == 404
