"""Paper embedding generation and semantic search."""

from __future__ import annotations

import math
from uuid import uuid4

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.llm.openai_provider import OpenAIProvider
from app.llm.router import LLMRouter
from app.models.paper import Paper, PaperEmbedding

logger = structlog.get_logger()


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    if not left or not right or len(left) != len(right):
        return 0.0

    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


class EmbeddingService:
    """Generate and query paper embeddings with pgvector or JSON fallback."""

    def __init__(self, db: AsyncSession, llm_router: LLMRouter | None = None):
        self.db = db
        self.llm_router = llm_router
        self.settings = get_settings()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        if not texts:
            return []

        provider_name = self.settings.embedding_provider
        model = self.settings.embedding_model

        if provider_name == "openai" and self.settings.openai_api_key:
            provider = OpenAIProvider(
                api_key=self.settings.openai_api_key,
                default_model=self.settings.openai_default_model,
            )
            return await provider.embed(texts, model=model)

        if self.llm_router:
            for provider in self.llm_router.providers.values():
                if hasattr(provider, "embed"):
                    return await provider.embed(texts, model=model)

        raise RuntimeError("No embedding provider configured")

    def _paper_embedding_text(self, paper: Paper) -> str:
        abstract = (paper.abstract or "").strip()
        if abstract:
            return f"{paper.title}\n{abstract[:2000]}"
        return paper.title

    async def embed_paper(self, paper_id: str) -> PaperEmbedding | None:
        """Create or refresh an embedding for a single paper."""
        paper = await self.db.get(Paper, paper_id)
        if not paper:
            return None

        vectors = await self.embed_texts([self._paper_embedding_text(paper)])
        return await self._upsert_embedding(paper_id, vectors[0])

    async def embed_papers_batch(self, paper_ids: list[str]) -> int:
        """Embed multiple papers in one provider call."""
        if not paper_ids:
            return 0

        result = await self.db.execute(select(Paper).where(Paper.id.in_(paper_ids)))
        papers = list(result.scalars().all())
        if not papers:
            return 0

        existing_result = await self.db.execute(
            select(PaperEmbedding.paper_id).where(PaperEmbedding.paper_id.in_(paper_ids)),
        )
        already_embedded = set(existing_result.scalars().all())
        pending = [paper for paper in papers if paper.id not in already_embedded]
        if not pending:
            return 0

        vectors = await self.embed_texts([self._paper_embedding_text(paper) for paper in pending])
        for paper, vector in zip(pending, vectors):
            await self._upsert_embedding(paper.id, vector)

        await self.db.flush()
        return len(pending)

    async def _upsert_embedding(self, paper_id: str, vector: list[float]) -> PaperEmbedding:
        result = await self.db.execute(
            select(PaperEmbedding).where(PaperEmbedding.paper_id == paper_id),
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.embedding = vector
            existing.model_name = self.settings.embedding_model
            await self.db.flush()
            await self._sync_pgvector_column(existing.id, vector)
            return existing

        record = PaperEmbedding(
            id=str(uuid4()),
            paper_id=paper_id,
            embedding=vector,
            model_name=self.settings.embedding_model,
        )
        self.db.add(record)
        await self.db.flush()
        await self._sync_pgvector_column(record.id, vector)
        return record

    async def _sync_pgvector_column(self, record_id: str, vector: list[float]) -> None:
        if not await self._pgvector_enabled():
            return
        vector_literal = "[" + ",".join(str(value) for value in vector) + "]"
        await self.db.execute(
            text(
                "UPDATE paper_embeddings "
                "SET embedding_vector = :vector::vector "
                "WHERE id = :record_id",
            ),
            {"vector": vector_literal, "record_id": record_id},
        )

    async def _pgvector_enabled(self) -> bool:
        bind = self.db.get_bind()
        if bind.dialect.name != "postgresql":
            return False
        try:
            result = await self.db.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"),
            )
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as exc:
            logger.warning("pgvector_check_failed", error=str(exc))
            return False
        except Exception as exc:
            logger.debug("pgvector_check_unexpected", error=str(exc))
            return False

    async def search_similar(
        self,
        project_id: str,
        query: str,
        *,
        limit: int = 10,
    ) -> list[dict]:
        """Search papers by semantic similarity to a natural-language query."""
        query_vector = (await self.embed_texts([query]))[0]

        if await self._pgvector_enabled():
            try:
                return await self._search_pgvector(project_id, query_vector, limit=limit)
            except SQLAlchemyError as exc:
                logger.warning("pgvector_search_db_error", error=str(exc))
            except Exception as exc:
                logger.warning("pgvector_search_failed", error=str(exc))

        return await self._search_json_cosine(project_id, query_vector, limit=limit)

    async def _search_pgvector(
        self,
        project_id: str,
        query_vector: list[float],
        *,
        limit: int,
    ) -> list[dict]:
        """Use pgvector distance when the extension and JSON embeddings are available."""
        vector_literal = "[" + ",".join(str(v) for v in query_vector) + "]"
        stmt = text(
            """
            SELECT p.id, p.title, p.year, p.doi,
                   (pe.embedding_vector <=> :query_vector::vector) AS distance
            FROM papers p
            JOIN paper_embeddings pe ON pe.paper_id = p.id
            WHERE p.project_id = :project_id
              AND pe.embedding_vector IS NOT NULL
            ORDER BY distance ASC
            LIMIT :limit
            """,
        )
        result = await self.db.execute(
            stmt,
            {
                "project_id": project_id,
                "query_vector": vector_literal,
                "limit": limit,
            },
        )
        rows = result.mappings().all()
        return [
            {
                "paper_id": row["id"],
                "title": row["title"],
                "year": row["year"],
                "doi": row["doi"],
                "score": max(0.0, 1.0 - float(row["distance"])),
            }
            for row in rows
        ]

    async def _search_json_cosine(
        self,
        project_id: str,
        query_vector: list[float],
        *,
        limit: int,
    ) -> list[dict]:
        """Fallback semantic search using cosine similarity over JSON embeddings."""
        result = await self.db.execute(
            select(Paper, PaperEmbedding)
            .join(PaperEmbedding, PaperEmbedding.paper_id == Paper.id)
            .where(Paper.project_id == project_id, PaperEmbedding.embedding.is_not(None)),
        )
        scored: list[tuple[float, Paper]] = []
        for paper, embedding in result.all():
            vector = embedding.embedding or []
            score = cosine_similarity(query_vector, vector)
            scored.append((score, paper))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "paper_id": paper.id,
                "title": paper.title,
                "year": paper.year,
                "doi": paper.doi,
                "score": round(score, 4),
            }
            for score, paper in scored[:limit]
        ]
