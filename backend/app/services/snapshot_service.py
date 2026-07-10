"""Snapshot export service for research runs."""

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idea import Idea, IdeaClassification, IdeaScore
from app.models.paper import ClusterConflict, Paper, PaperCluster
from app.models.research_question import Hypothesis, ResearchQuestion, ValidationPlan
from app.models.research_run import ResearchRun, ResearchRunEvent, ToolCall
from app.schemas.research_state import (
    ClusterSummary,
    ConflictSummary,
    EventRecord,
    HypothesisSummary,
    PaperSummary,
    QuestionSummary,
    ResearchState,
    RunBudget,
    RunState,
    RunType,
    ScoreSummary,
    ToolCallRecord,
)

from .manuscript_context_service import ManuscriptContextService


class SnapshotService:
    """Service for creating run snapshots."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_snapshot(self, run_id: str) -> ResearchState | None:
        """Create a complete snapshot of a research run's state."""
        result = await self.db.execute(select(ResearchRun).where(ResearchRun.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            return None

        idea = await self._get_idea(run.idea_id) if run.idea_id else None
        clusters = await self._get_clusters(run.project_id, run_id)
        conflicts = await self._get_conflicts(run.project_id, run_id)
        paper_ids = {pid for cluster in clusters for pid in (cluster.paper_ids or [])}
        papers = await self._get_papers(run.project_id, paper_ids or None)
        questions = await self._get_questions(run.project_id, run_id)
        question_ids = {question.id for question in questions}
        hypotheses = await self._get_hypotheses(run.project_id, question_ids or None)
        scores = await self._get_scores(run.idea_id) if run.idea_id else []
        events = await self._get_events(run_id)
        tool_calls = await self._get_tool_calls(run_id)
        keywords = await self._get_keywords_from_events(run_id)
        experiment = await self._get_experiment_context(run_id)

        try:
            run_state = RunState(run.state)
        except ValueError:
            run_state = RunState.CREATED

        latest_score = scores[-1] if scores else None
        state = ResearchState(
            run_id=run.id,
            project_id=run.project_id,
            idea_id=run.idea_id,
            run_type=RunType(run.run_type),
            current_phase=run.current_phase or "initialized",
            state=run_state,
            original_idea=idea.initial_text if idea else "",
            current_idea=idea.current_text if idea else "",
            flexibility=idea.flexibility if idea else 0.6,
            budget=RunBudget(
                max_minutes=run.max_minutes,
                max_sources=run.max_sources,
                max_cost_usd=run.max_cost_usd,
            ),
            cognitive_entropy=run.cognitive_entropy or 0.0,
            cognitive_mode=run.cognitive_mode or "exploring",
            keywords=keywords,
            papers=papers,
            clusters=clusters,
            conflicts=conflicts,
            questions=questions,
            hypotheses=hypotheses,
            scores=scores,
            current_classification=idea.classification if idea else None,
            experiment_code=experiment.get("script") if experiment else None,
            experiment_result=experiment,
            sources_searched=len(papers),
            cost_usd=latest_score.cost_usd if latest_score and latest_score.cost_usd else 0.0,
            events=events,
            tool_calls=tool_calls,
            started_at=run.started_at,
            completed_at=run.completed_at,
            last_updated=run.updated_at or run.created_at,
        )

        return state

    async def _get_idea(self, idea_id: str) -> Idea | None:
        """Get an idea by ID."""
        result = await self.db.execute(select(Idea).where(Idea.id == idea_id))
        return result.scalar_one_or_none()

    async def _get_papers(
        self,
        project_id: str,
        paper_ids: set[str] | None = None,
    ) -> list[PaperSummary]:
        """Get papers for a run, preferring cluster-linked IDs when available."""
        if paper_ids:
            result = await self.db.execute(
                select(Paper).where(Paper.id.in_(paper_ids)),
            )
        else:
            result = await self.db.execute(
                select(Paper).where(Paper.project_id == project_id).limit(100),
            )
        papers = result.scalars().all()

        return [
            PaperSummary(
                id=p.id,
                title=p.title,
                authors=p.authors or [],
                year=p.year,
                doi=p.doi,
                citation_count=p.citation_count,
                paper_type=p.paper_type,
                references=p.references or [],
            )
            for p in papers
        ]

    async def _get_clusters(
        self,
        project_id: str,
        run_id: str | None = None,
    ) -> list[ClusterSummary]:
        """Get clusters for a project as summaries, scoped to a run when possible."""
        query = select(PaperCluster).where(PaperCluster.project_id == project_id)
        if run_id:
            query = query.where(PaperCluster.run_id == run_id)

        result = await self.db.execute(query)
        clusters = result.scalars().all()

        return [
            ClusterSummary(
                id=c.id,
                name=c.name,
                description=c.description,
                cluster_type=c.cluster_type,
                paper_count=len(c.paper_ids) if c.paper_ids else 0,
                paper_ids=c.paper_ids or [],
                representative_paper_id=c.representative_paper_id,
            )
            for c in clusters
        ]

    async def _get_conflicts(
        self,
        project_id: str,
        run_id: str | None = None,
    ) -> list[ConflictSummary]:
        """Get conflicts for a project as summaries, scoped to a run when possible."""
        query = select(ClusterConflict).where(ClusterConflict.project_id == project_id)
        if run_id:
            query = query.where(ClusterConflict.run_id == run_id)

        result = await self.db.execute(query)
        conflicts = result.scalars().all()

        return [
            ConflictSummary(
                id=c.id,
                conflict_type=c.conflict_type,
                description=c.description,
                severity=c.severity,
                supporting_papers_count=len(c.supporting_papers) if c.supporting_papers else 0,
                opposing_papers_count=len(c.opposing_papers) if c.opposing_papers else 0,
            )
            for c in conflicts
        ]

    async def _get_questions(
        self, project_id: str, run_id: str | None = None,
    ) -> list[QuestionSummary]:
        """Get questions for a project as summaries."""
        query = select(ResearchQuestion).where(ResearchQuestion.project_id == project_id)
        if run_id:
            query = query.where(ResearchQuestion.run_id == run_id)

        result = await self.db.execute(query)
        questions = result.scalars().all()

        return [
            QuestionSummary(
                id=q.id,
                question=q.question,
                rank=q.rank,
                status=q.status,
                source_conflicts_count=len(q.source_conflicts) if q.source_conflicts else 0,
            )
            for q in questions
        ]

    async def _get_hypotheses(
        self,
        project_id: str,
        question_ids: set[str] | None = None,
    ) -> list[HypothesisSummary]:
        """Get hypotheses for a project, optionally scoped to run-linked questions."""
        query = select(Hypothesis).where(Hypothesis.project_id == project_id)
        if question_ids:
            query = query.where(Hypothesis.question_id.in_(question_ids))

        result = await self.db.execute(query)
        hypotheses = result.scalars().all()

        summaries = []
        for h in hypotheses:
            vp_result = await self.db.execute(
                select(ValidationPlan).where(ValidationPlan.hypothesis_id == h.id),
            )
            has_vp = vp_result.scalar_one_or_none() is not None

            summaries.append(
                HypothesisSummary(
                    id=h.id,
                    statement=h.statement,
                    confidence=h.confidence,
                    status=h.status,
                    has_validation_plan=has_vp,
                ),
            )

        return summaries

    async def _get_scores(self, idea_id: str) -> list[ScoreSummary]:
        """Get scores for an idea as summaries."""
        result = await self.db.execute(
            select(IdeaScore)
            .where(IdeaScore.idea_id == idea_id)
            .order_by(IdeaScore.created_at),
        )
        scores = result.scalars().all()

        classification_result = await self.db.execute(
            select(IdeaClassification)
            .where(IdeaClassification.idea_id == idea_id)
            .order_by(IdeaClassification.created_at.desc())
            .limit(1),
        )
        latest_classification = classification_result.scalar_one_or_none()

        return [
            ScoreSummary(
                id=s.id,
                novelty=s.novelty,
                feasibility=s.feasibility,
                importance=s.importance,
                evidence_support=s.evidence_support,
                validation_clarity=s.validation_clarity,
                differentiation=s.differentiation,
                data_availability=s.data_availability,
                skill_leverage=s.skill_leverage,
                user_alignment=s.user_alignment,
                prior_art_risk=s.prior_art_risk,
                safety_risk=s.safety_risk,
                cost_risk=s.cost_risk,
                overall_value=s.overall_value,
                classification=latest_classification.classification if latest_classification else None,
                rationale=s.scoring_rationale,
                scored_at=s.created_at,
                cost_usd=s.cost_usd,
            )
            for s in scores
        ]

    async def _get_events(self, run_id: str) -> list[EventRecord]:
        """Get events for a run as records."""
        result = await self.db.execute(
            select(ResearchRunEvent)
            .where(ResearchRunEvent.run_id == run_id)
            .order_by(ResearchRunEvent.created_at),
        )
        events = result.scalars().all()

        return [
            EventRecord(
                id=e.id,
                event_type=e.event_type,
                actor=e.actor,
                timestamp=e.created_at,
            )
            for e in events
        ]

    async def _get_tool_calls(self, run_id: str) -> list[ToolCallRecord]:
        """Get tool calls for a run as records."""
        result = await self.db.execute(
            select(ToolCall)
            .where(ToolCall.run_id == run_id)
            .order_by(ToolCall.created_at),
        )
        tool_calls = result.scalars().all()

        return [
            ToolCallRecord(
                id=tc.id,
                tool_name=tc.tool_name,
                agent_role=tc.agent_role,
                duration_ms=tc.duration_ms,
                success=tc.success,
                timestamp=tc.created_at,
            )
            for tc in tool_calls
        ]

    async def _get_keywords_from_events(self, run_id: str) -> list[str]:
        """Restore expanded search keywords from the latest keywords event."""
        result = await self.db.execute(
            select(ResearchRunEvent)
            .where(
                ResearchRunEvent.run_id == run_id,
                ResearchRunEvent.event_type == "keywords",
            )
            .order_by(ResearchRunEvent.created_at.desc())
            .limit(1),
        )
        event = result.scalar_one_or_none()
        if not event or not event.details:
            return []
        keywords = event.details.get("keywords")
        return keywords if isinstance(keywords, list) else []

    async def _get_experiment_context(self, run_id: str) -> dict[str, Any] | None:
        """Load persisted sandbox experiment output for a run."""
        context_service = ManuscriptContextService(self.db)
        return await context_service.get_experiment_for_run(run_id)

    async def export_snapshot_json(self, run_id: str) -> str | None:
        """Export a run snapshot as JSON string."""
        state = await self.create_snapshot(run_id)
        if not state:
            return None
        return json.dumps(state.to_snapshot(), indent=2, default=str)

    async def export_snapshot_dict(self, run_id: str) -> dict[str, Any] | None:
        """Export a run snapshot as dictionary."""
        state = await self.create_snapshot(run_id)
        if not state:
            return None
        return state.to_snapshot()
