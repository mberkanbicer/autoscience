"""Unified persistence for research workflow results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import structlog
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.base import RawPaper
from app.engine.deduplication import (
    ExistingPaperRecord,
    deduplicate_papers,
    find_duplicate_in_existing,
)
from app.llm.router import LLMRouter
from app.models.idea import IdeaScore
from app.models.paper import ClusterConflict, Paper, PaperCluster
from app.models.research_question import Hypothesis, ResearchQuestion
from app.models.research_run import ResearchRun
from app.schemas.research_state import PaperSummary, ResearchState
from app.services.embedding_service import EmbeddingService

logger = structlog.get_logger()


@dataclass
class PersistenceResult:
    """Summary of a persistence operation."""

    stored: dict[str, int] = field(default_factory=dict)
    skipped: dict[str, int] = field(default_factory=dict)
    paper_id_map: dict[str, str] = field(default_factory=dict)
    new_paper_ids: list[str] = field(default_factory=list)
    embeddings_created: int = 0


def _safe_get(obj: Any, field: str, default=None):
    try:
        if hasattr(obj, "model_dump"):
            return obj.model_dump().get(field, default)
        if hasattr(obj, field):
            return getattr(obj, field, default)
        return default
    except Exception as exc:
        logger.debug("safe_get_failed", field=field, error=str(exc))
        return default


def paper_summary_to_raw(paper: PaperSummary) -> RawPaper:
    """Convert workflow paper summary to connector RawPaper for deduplication."""
    return RawPaper(
        source="workflow",
        source_id=paper.id,
        title=paper.title,
        authors=paper.authors or [],
        year=paper.year,
        doi=paper.doi,
        abstract=_safe_get(paper, "abstract"),
        venue=_safe_get(paper, "venue"),
        citation_count=paper.citation_count,
        paper_type=paper.paper_type,
        references=paper.references or [],
    )


class ResearchPersistenceService:
    """Persist research workflow state with batch deduplication and embeddings."""

    def __init__(self, db: AsyncSession, llm_router: LLMRouter | None = None):
        self.db = db
        self.embedding_service = EmbeddingService(db, llm_router)

    async def persist_run_results(self, state: ResearchState) -> PersistenceResult:
        """Persist all workflow artifacts for a completed or paused run."""
        result = PersistenceResult(
            stored={
                "papers": 0,
                "clusters": 0,
                "conflicts": 0,
                "questions": 0,
                "hypotheses": 0,
                "scores": 0,
            },
            skipped={
                "papers": 0,
                "questions": 0,
                "hypotheses": 0,
            },
        )

        paper_map, new_paper_ids = await self._persist_papers(state, result)
        result.paper_id_map = paper_map
        result.new_paper_ids = new_paper_ids
        await self._persist_clusters(state, result)
        await self._persist_conflicts(state, result)
        await self._persist_questions(state, result)
        await self._persist_hypotheses(state, result)
        await self._persist_scores(state, result)
        await self._update_run_metrics(state)
        result.embeddings_created = await self._embed_new_papers(result)

        await self.db.flush()
        logger.info(
            "persist_run_results_done",
            stored=result.stored,
            skipped=result.skipped,
            embeddings=result.embeddings_created,
        )
        return result

    async def _load_existing_papers(self, project_id: str) -> list[ExistingPaperRecord]:
        rows = await self.db.execute(
            select(Paper.id, Paper.title, Paper.doi).where(Paper.project_id == project_id),
        )
        return [
            ExistingPaperRecord(id=row.id, title=row.title, doi=row.doi)
            for row in rows.all()
        ]

    async def _persist_papers(
        self,
        state: ResearchState,
        result: PersistenceResult,
    ) -> tuple[dict[str, str], list[str]]:
        paper_id_map: dict[str, str] = {}
        new_paper_ids: list[str] = []
        if not state.papers:
            return paper_id_map, new_paper_ids

        raw_papers = [paper_summary_to_raw(paper) for paper in state.papers]
        deduped = deduplicate_papers(raw_papers)
        existing_records = await self._load_existing_papers(state.project_id)

        for raw in deduped:
            state_id = raw.source_id
            try:
                existing_id = find_duplicate_in_existing(raw, existing_records)
                if existing_id:
                    paper_id_map[state_id] = existing_id
                    result.skipped["papers"] += 1
                    continue

                db_paper = Paper(
                    id=str(uuid4()),
                    project_id=state.project_id,
                    title=raw.title,
                    authors=raw.authors,
                    year=raw.year,
                    doi=raw.doi,
                    abstract=raw.abstract,
                    venue=raw.venue,
                    citation_count=raw.citation_count,
                    paper_type=raw.paper_type,
                    references=raw.references or [],
                )
                self.db.add(db_paper)
                paper_id_map[state_id] = db_paper.id
                new_paper_ids.append(db_paper.id)
                existing_records.append(
                    ExistingPaperRecord(id=db_paper.id, title=raw.title, doi=raw.doi),
                )
                result.stored["papers"] += 1
            except (TypeError, ValueError, SQLAlchemyError) as exc:
                logger.warning("store_paper_failed", title=raw.title[:50], error=str(exc))
            except Exception as exc:
                logger.warning("store_paper_unexpected", title=raw.title[:50], error=str(exc))

        for paper in state.papers:
            if paper.id not in paper_id_map:
                duplicate_id = find_duplicate_in_existing(
                    paper_summary_to_raw(paper),
                    existing_records,
                )
                if duplicate_id:
                    paper_id_map[paper.id] = duplicate_id

        return paper_id_map, new_paper_ids

    async def _persist_clusters(self, state: ResearchState, result: PersistenceResult) -> None:
        paper_id_map = result.paper_id_map
        for cluster in state.clusters:
            try:
                mapped_ids = [
                    paper_id_map.get(paper_id, paper_id)
                    for paper_id in (cluster.paper_ids or [])
                ]
                db_cluster = PaperCluster(
                    id=cluster.id or str(uuid4()),
                    project_id=state.project_id,
                    run_id=state.run_id,
                    name=cluster.name,
                    description=cluster.description,
                    cluster_type=cluster.cluster_type or "topic",
                    paper_ids=mapped_ids,
                    representative_paper_id=cluster.representative_paper_id,
                )
                self.db.add(db_cluster)
                result.stored["clusters"] += 1
            except (TypeError, ValueError, SQLAlchemyError) as exc:
                logger.warning("store_cluster_failed", error=str(exc))
            except Exception as exc:
                logger.warning("store_cluster_unexpected", error=str(exc))

    async def _persist_conflicts(self, state: ResearchState, result: PersistenceResult) -> None:
        for conflict in state.conflicts:
            try:
                db_conflict = ClusterConflict(
                    id=conflict.id or str(uuid4()),
                    project_id=state.project_id,
                    run_id=state.run_id,
                    conflict_type=conflict.conflict_type,
                    description=conflict.description,
                    severity=conflict.severity or 0.5,
                    research_opportunity=f"Investigate {conflict.conflict_type} conflict",
                )
                self.db.add(db_conflict)
                result.stored["conflicts"] += 1
            except (TypeError, ValueError, SQLAlchemyError) as exc:
                logger.warning("store_conflict_failed", error=str(exc))
            except Exception as exc:
                logger.warning("store_conflict_unexpected", error=str(exc))

    async def _persist_questions(self, state: ResearchState, result: PersistenceResult) -> None:
        existing_q_result = await self.db.execute(
            select(ResearchQuestion.question).where(ResearchQuestion.project_id == state.project_id),
        )
        existing_question_texts = {q.strip().lower() for q in existing_q_result.scalars().all()}

        for question in state.questions:
            try:
                normalized_q = question.question.strip().lower()
                if normalized_q in existing_question_texts:
                    result.skipped["questions"] += 1
                    continue
                db_question = ResearchQuestion(
                    id=question.id or str(uuid4()),
                    project_id=state.project_id,
                    run_id=state.run_id,
                    idea_id=state.idea_id,
                    question=question.question,
                    rank=question.rank,
                    status="generated",
                )
                self.db.add(db_question)
                existing_question_texts.add(normalized_q)
                result.stored["questions"] += 1
            except (TypeError, ValueError, SQLAlchemyError) as exc:
                logger.warning("store_question_failed", error=str(exc))
            except Exception as exc:
                logger.warning("store_question_unexpected", error=str(exc))

    async def _persist_hypotheses(self, state: ResearchState, result: PersistenceResult) -> None:
        existing_h_result = await self.db.execute(
            select(Hypothesis.statement).where(Hypothesis.project_id == state.project_id),
        )
        existing_hypothesis_stmts = {s.strip().lower() for s in existing_h_result.scalars().all()}

        for hypothesis in state.hypotheses:
            try:
                normalized_stmt = hypothesis.statement.strip().lower()
                if normalized_stmt in existing_hypothesis_stmts:
                    result.skipped["hypotheses"] += 1
                    continue
                db_hypothesis = Hypothesis(
                    id=hypothesis.id or str(uuid4()),
                    project_id=state.project_id,
                    idea_id=state.idea_id,
                    statement=hypothesis.statement,
                    confidence=hypothesis.confidence,
                    version=1,
                    status="draft",
                )
                self.db.add(db_hypothesis)
                existing_hypothesis_stmts.add(normalized_stmt)
                result.stored["hypotheses"] += 1
            except (TypeError, ValueError, SQLAlchemyError) as exc:
                logger.warning("store_hypothesis_failed", error=str(exc))
            except Exception as exc:
                logger.warning("store_hypothesis_unexpected", error=str(exc))

    async def _persist_scores(self, state: ResearchState, result: PersistenceResult) -> None:
        if not (state.scores and state.idea_id):
            return
        try:
            score = state.scores[0]
            db_score = IdeaScore(
                id=str(uuid4()),
                idea_id=state.idea_id,
                novelty=_safe_get(score, "novelty"),
                feasibility=_safe_get(score, "feasibility"),
                importance=_safe_get(score, "importance"),
                evidence_support=_safe_get(score, "evidence_support"),
                validation_clarity=_safe_get(score, "validation_clarity"),
                differentiation=_safe_get(score, "differentiation"),
                data_availability=_safe_get(score, "data_availability"),
                skill_leverage=_safe_get(score, "skill_leverage"),
                user_alignment=_safe_get(score, "user_alignment"),
                prior_art_risk=_safe_get(score, "prior_art_risk"),
                safety_risk=_safe_get(score, "safety_risk"),
                cost_risk=_safe_get(score, "cost_risk"),
                overall_value=_safe_get(score, "overall_value"),
                scoring_rationale=_safe_get(score, "rationale")
                or "Auto-scored during research workflow",
                cost_usd=state.cost_usd,
            )
            self.db.add(db_score)
            result.stored["scores"] += 1
        except (TypeError, ValueError, SQLAlchemyError) as exc:
            logger.warning("store_score_failed", error=str(exc))
        except Exception as exc:
            logger.warning("store_score_unexpected", error=str(exc))

    async def _update_run_metrics(self, state: ResearchState) -> None:
        if not state.run_id:
            return
        try:
            await self.db.execute(
                update(ResearchRun)
                .where(ResearchRun.id == state.run_id)
                .values(
                    cognitive_entropy=state.cognitive_entropy,
                    cognitive_mode=state.cognitive_mode,
                ),
            )
        except SQLAlchemyError as exc:
            logger.warning("update_run_metrics_failed", error=str(exc))
        except Exception as exc:
            logger.warning("update_run_metrics_unexpected", error=str(exc))

    async def _embed_new_papers(self, result: PersistenceResult) -> int:
        if not result.new_paper_ids:
            return 0
        try:
            return await self.embedding_service.embed_papers_batch(result.new_paper_ids)
        except SQLAlchemyError as exc:
            logger.warning("batch_embed_failed", error=str(exc))
            return 0
        except Exception as exc:
            logger.warning("batch_embed_unexpected", error=str(exc))
            return 0
