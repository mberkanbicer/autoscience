"""Semantic search over wiki knowledge notes using stored embeddings."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import KnowledgeNote
from app.services.embedding_service import EmbeddingService, cosine_similarity


class WikiEmbeddingService:
    """Embed and search knowledge notes by semantic similarity."""

    def __init__(self, db: AsyncSession, embedding_service: EmbeddingService):
        self.db = db
        self.embedding_service = embedding_service

    def _note_text(self, note: KnowledgeNote) -> str:
        title = (note.title or "").strip()
        content = (note.content or "").strip()[:3000]
        return f"{title}\n{content}".strip()

    async def embed_note(self, note_id: str) -> KnowledgeNote | None:
        note = await self.db.get(KnowledgeNote, note_id)
        if not note:
            return None
        text = self._note_text(note)
        if not text:
            return note
        vector = (await self.embedding_service.embed_texts([text]))[0]
        note.embedding = vector
        await self.db.flush()
        return note

    async def embed_project_notes(self, project_id: str, *, limit: int = 200) -> int:
        result = await self.db.execute(
            select(KnowledgeNote)
            .where(KnowledgeNote.project_id == project_id)
            .order_by(KnowledgeNote.updated_at.desc())
            .limit(limit),
        )
        notes = [n for n in result.scalars().all() if not n.embedding and self._note_text(n)]
        if not notes:
            return 0

        vectors = await self.embedding_service.embed_texts([self._note_text(n) for n in notes])
        for note, vector in zip(notes, vectors):
            note.embedding = vector
        await self.db.flush()
        return len(notes)

    async def search_semantic(
        self,
        project_id: str,
        query: str,
        *,
        run_id: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        await self.embed_project_notes(project_id)
        query_vector = (await self.embedding_service.embed_texts([query]))[0]

        stmt = select(KnowledgeNote).where(KnowledgeNote.project_id == project_id)
        if run_id:
            stmt = stmt.where(KnowledgeNote.run_id == run_id)
        result = await self.db.execute(stmt)
        notes = list(result.scalars().all())

        scored: list[tuple[float, KnowledgeNote]] = []
        for note in notes:
            vector = note.embedding or []
            if not vector:
                continue
            scored.append((cosine_similarity(query_vector, vector), note))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "note_id": note.id,
                "title": note.title,
                "note_type": note.note_type,
                "run_id": note.run_id,
                "score": round(score, 4),
                "snippet": (note.content or "")[:300],
            }
            for score, note in scored[:limit]
            if score > 0.1
        ]
