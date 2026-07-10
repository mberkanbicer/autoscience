"""Tests for arXiv search and DOI/arXiv import endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.connectors.base import RawPaper


def _sample_raw_paper(**overrides) -> RawPaper:
    defaults = {
        "source": "crossref",
        "source_id": "10.1234/example",
        "title": "Sample Paper",
        "authors": ["A Author"],
        "year": 2024,
        "doi": "10.1234/example",
        "abstract": "An abstract.",
        "venue": "Journal",
        "url": "https://doi.org/10.1234/example",
        "citation_count": 10,
        "paper_type": "research",
    }
    defaults.update(overrides)
    return RawPaper(**defaults)


@pytest.mark.asyncio
async def test_arxiv_search(client: AsyncClient):
    mock_result = type("Result", (), {"papers": [_sample_raw_paper(source="arxiv", source_id="2301.00001")]})()
    with patch("app.connectors.arxiv.ArxivConnector") as mock_cls:
        mock_cls.return_value.search = AsyncMock(return_value=mock_result)
        response = await client.get("/api/v1/papers/arxiv/search?q=transformer&limit=5")

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "transformer"
    assert len(data["papers"]) == 1
    assert data["papers"][0]["source_id"] == "2301.00001"


@pytest.mark.asyncio
async def test_resolve_doi_creates_paper(client: AsyncClient, sample_project):
    headers = {"X-User-Email": "editor@test.com", "X-User-Name": "Editor"}
    with patch("app.connectors.crossref.CrossrefConnector") as mock_cls:
        mock_cls.return_value.get_paper = AsyncMock(
            return_value=_sample_raw_paper(doi="10.1234/example", source_id="10.1234/example")
        )
        response = await client.post(
            f"/api/v1/papers/resolve-doi?project_id={sample_project.id}&doi=10.1234/example",
            headers=headers,
        )

    assert response.status_code == 200
    assert response.json()["doi"] == "10.1234/example"
    assert response.json()["title"] == "Sample Paper"


@pytest.mark.asyncio
async def test_import_arxiv_creates_paper(client: AsyncClient, sample_project):
    headers = {"X-User-Email": "editor@test.com", "X-User-Name": "Editor"}
    with patch("app.connectors.arxiv.ArxivConnector") as mock_cls:
        mock_cls.return_value.get_paper = AsyncMock(
            return_value=_sample_raw_paper(
                source="arxiv",
                source_id="2301.00001",
                doi=None,
                url="https://arxiv.org/abs/2301.00001",
            )
        )
        response = await client.post(
            f"/api/v1/papers/import-arxiv?project_id={sample_project.id}&source_id=2301.00001",
            headers=headers,
        )

    assert response.status_code == 200
    assert response.json()["source_connector"] == "arxiv"
    assert response.json()["source_id"] == "2301.00001"