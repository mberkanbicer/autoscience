"""Tests for wiki semantic search."""

import pytest

from app.models.report import KnowledgeNote
from app.services.embedding_service import cosine_similarity
from app.services.wiki_embedding_service import WikiEmbeddingService


class FakeEmbeddingService:
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] if "transformer" in t.lower() else [0.0, 1.0] for t in texts]


@pytest.mark.asyncio
async def test_wiki_semantic_search_ranks_by_similarity(db_session, sample_project):
    note_a = KnowledgeNote(
        id="note-a",
        project_id=sample_project.id,
        note_type="paper",
        title="Transformer efficiency",
        content="Notes about transformer architectures",
        embedding=[1.0, 0.0],
    )
    note_b = KnowledgeNote(
        id="note-b",
        project_id=sample_project.id,
        note_type="paper",
        title="Climate datasets",
        content="Temperature records over decades",
        embedding=[0.0, 1.0],
    )
    db_session.add_all([note_a, note_b])
    await db_session.flush()

    service = WikiEmbeddingService(db_session, FakeEmbeddingService())
    results = await service.search_semantic(sample_project.id, "transformer models")

    assert results
    assert results[0]["note_id"] == "note-a"
    assert results[0]["score"] == pytest.approx(1.0, abs=0.01)


def test_cosine_similarity_identical():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)