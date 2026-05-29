"""Snapshot export service for research runs."""

import json
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.research_run import ResearchRun, ResearchRunEvent, ToolCall
from ..models.idea import Idea, IdeaScore, IdeaClassification
from ..models.paper import Paper, PaperAnalysis, PaperCluster, ClusterConflict
from ..models.research_question import ResearchQuestion, Hypothesis, ValidationPlan
from ..models.skill import Skill, SkillUsage
from ..schemas.research_state import (
    ResearchState,
    RunType,
    RunState,
    RunBudget,
    PaperSummary,
    ClusterSummary,
    ConflictSummary,
    QuestionSummary,
    HypothesisSummary,
    ScoreSummary,
    EventRecord,
    ToolCallRecord,
)


class SnapshotService:
    """Service for creating run snapshots."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_snapshot(self, run_id: str) -> ResearchState | None:
        """Create a complete snapshot of a research run's state."""
        # Get the run
        result = await self.db.execute(select(ResearchRun).where(ResearchRun.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            return None

        # Get related data
        idea = await self._get_idea(run.idea_id) if run.idea_id else None
        papers = await self._get_papers(run.project_id)
        clusters = await self._get_clusters(run.project_id)
        conflicts = await self._get_conflicts(run.project_id)
        questions = await self._get_questions(run.project_id, run_id)
        hypotheses = await self._get_hypotheses(run.project_id)
        scores = await self._get_scores(run.idea_id) if run.idea_id else None
        events = await self._get_events(run_id)
        tool_calls = await self._get_tool_calls(run_id)

        # Build the state
        state = ResearchState(
            run_id=run.id,
            project_id=run.project_id,
            idea_id=run.idea_id,
            run_type=RunType(run.run_type),
            state=RunState(run.state),
            original_idea=idea.initial_text if idea else "",
            current_idea=idea.current_text if idea else "",
            flexibility=idea.flexibility if idea else 0.6,
            budget=RunBudget(
                max_minutes=run.max_minutes,
                max_sources=run.max_sources,
                max_cost_usd=run.max_cost_usd,
            ),
            papers=papers,
            clusters=clusters,
            conflicts=conflicts,
            questions=questions,
            hypotheses=hypotheses,
            scores=scores or [],
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

    async def _get_papers(self, project_id: str) -> list[PaperSummary]:
        """Get papers for a project as summaries."""
        result = await self.db.execute(
            select(Paper).where(Paper.project_id == project_id).limit(100)
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
            )
            for p in papers
        ]

    async def _get_clusters(self, project_id: str) -> list[ClusterSummary]:
        """Get clusters for a project as summaries."""
        from ..models.paper import PaperCluster

        result = await self.db.execute(
            select(PaperCluster).where(PaperCluster.project_id == project_id)
        )
        clusters = result.scalars().all()

        return [
            ClusterSummary(
                id=c.id,
                name=c.name,
                description=c.description,
                cluster_type=c.cluster_type,
                paper_count=len(c.paper_ids) if c.paper_ids else 0,
                representative_paper_id=c.representative_paper_id,
            )
            for c in clusters
        ]

    async def _get_conflicts(self, project_id: str) -> list[ConflictSummary]:
        """Get conflicts for a project as summaries."""
        from ..models.paper import ClusterConflict

        result = await self.db.execute(
            select(ClusterConflict).where(ClusterConflict.project_id == project_id)
        )
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
        self, project_id: str, run_id: str | None = None
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

    async def _get_hypotheses(self, project_id: str) -> list[HypothesisSummary]:
        """Get hypotheses for a project as summaries."""
        result = await self.db.execute(
            select(Hypothesis).where(Hypothesis.project_id == project_id)
        )
        hypotheses = result.scalars().all()

        summaries = []
        for h in hypotheses:
            # Check if validation plan exists
            vp_result = await self.db.execute(
                select(ValidationPlan).where(ValidationPlan.hypothesis_id == h.id)
            )
            has_vp = vp_result.scalar_one_or_none() is not None

            summaries.append(
                HypothesisSummary(
                    id=h.id,
                    statement=h.statement,
                    confidence=h.confidence,
                    status=h.status,
                    has_validation_plan=has_vp,
                )
            )

        return summaries

    async def _get_scores(self, idea_id: str) -> list[ScoreSummary]:
        """Get scores for an idea as summaries."""
        result = await self.db.execute(
            select(IdeaScore).where(IdeaScore.idea_id == idea_id)
        )
        scores = result.scalars().all()

        return [
            ScoreSummary(
                id=s.id,
                overall_value=s.overall_value,
                classification=None,  # Would need to join with classifications
                scored_at=s.created_at,
            )
            for s in scores
        ]

    async def _get_events(self, run_id: str) -> list[EventRecord]:
        """Get events for a run as records."""
        result = await self.db.execute(
            select(ResearchRunEvent)
            .where(ResearchRunEvent.run_id == run_id)
            .order_by(ResearchRunEvent.created_at)
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
            .order_by(ToolCall.created_at)
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
