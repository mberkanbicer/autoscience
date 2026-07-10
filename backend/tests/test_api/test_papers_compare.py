"""Tests for paper comparison and citation graph."""

import pytest
from httpx import AsyncClient

from app.models.paper import Paper, PaperAnalysis


@pytest.mark.asyncio
async def test_compare_papers_requires_two_ids(client: AsyncClient, db_session, sample_project):
    paper_a = Paper(
        id="paper-a",
        project_id=sample_project.id,
        title="Alpha Paper",
        authors=["A Author"],
        year=2024,
    )
    paper_b = Paper(
        id="paper-b",
        project_id=sample_project.id,
        title="Beta Paper",
        authors=["B Author"],
        year=2023,
    )
    db_session.add_all([paper_a, paper_b])
    db_session.add(
        PaperAnalysis(
            id="analysis-a",
            paper_id="paper-a",
            problem="Problem A",
            method="Method A",
            findings=["Finding A"],
        )
    )
    await db_session.commit()

    response = await client.get("/api/v1/papers/compare?ids=paper-a,paper-b")
    assert response.status_code == 200
    data = response.json()
    assert len(data["papers"]) == 2
    assert data["papers"][0]["method"] == "Method A"


@pytest.mark.asyncio
async def test_citation_graph(client: AsyncClient, db_session, sample_project):
    source = Paper(
        id="paper-src",
        project_id=sample_project.id,
        title="Source Paper",
        references=["Target Paper"],
    )
    target = Paper(
        id="paper-tgt",
        project_id=sample_project.id,
        title="Target Paper",
        references=[],
    )
    db_session.add_all([source, target])
    await db_session.commit()

    response = await client.get(f"/api/v1/papers/citation-graph?project_id={sample_project.id}")
    assert response.status_code == 200
    graph = response.json()
    assert len(graph["nodes"]) == 2
    assert any(e["source"] == "paper-src" for e in graph["edges"])