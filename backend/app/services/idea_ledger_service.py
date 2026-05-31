"""Idea ledger service for comprehensive idea management."""

from uuid import uuid4
from typing import Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from ..models.idea import Idea, IdeaVersion, IdeaScore, IdeaClassification, IdeaDecision
from ..models.paper import Paper
from ..models.research_question import ResearchQuestion, Hypothesis
from ..models.skill import Skill


class IdeaLedgerService:
    """Service for comprehensive idea management and ledger operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_idea(
        self,
        project_id: str,
        text: str,
        origin: str = "user_prompt",
        flexibility: float | None = None,
    ) -> Idea:
        """Create a new idea with initial version.

        If an idea with the same text already exists for this project,
        return the existing one instead of creating a duplicate.
        """
        normalized_text = text.strip()
        result = await self.db.execute(
            select(Idea).where(
                Idea.project_id == project_id,
                Idea.current_text == normalized_text,
            ).limit(1)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        idea = Idea(
            id=str(uuid4()),
            project_id=project_id,
            origin=origin,
            initial_text=text,
            current_text=text,
            flexibility=flexibility,
            status="active",
        )
        self.db.add(idea)

        # Create initial version
        version = IdeaVersion(
            id=str(uuid4()),
            idea_id=idea.id,
            version_number=1,
            text=text,
            change_reason="Initial idea",
        )
        self.db.add(version)

        await self.db.flush()
        return idea

    async def get_idea(self, idea_id: str) -> Idea | None:
        """Get an idea by ID."""
        result = await self.db.execute(select(Idea).where(Idea.id == idea_id))
        return result.scalar_one_or_none()

    async def update_idea_text(
        self,
        idea_id: str,
        new_text: str,
        change_reason: str = "Updated via API",
    ) -> Idea | None:
        """Update idea text and create new version."""
        idea = await self.get_idea(idea_id)
        if not idea:
            return None

        # Get current version number
        version_result = await self.db.execute(
            select(IdeaVersion)
            .where(IdeaVersion.idea_id == idea_id)
            .order_by(IdeaVersion.version_number.desc())
            .limit(1)
        )
        current_version = version_result.scalar_one_or_none()
        next_version = (current_version.version_number + 1) if current_version else 1

        # Create new version
        new_version = IdeaVersion(
            id=str(uuid4()),
            idea_id=idea_id,
            version_number=next_version,
            text=new_text,
            change_reason=change_reason,
        )
        self.db.add(new_version)

        # Update idea
        idea.current_text = new_text

        await self.db.flush()
        return idea

    async def add_score(
        self,
        idea_id: str,
        scores: dict[str, float],
        rationale: str | None = None,
    ) -> IdeaScore:
        """Add a score record to an idea."""
        score = IdeaScore(
            id=str(uuid4()),
            idea_id=idea_id,
            novelty=scores.get("novelty"),
            feasibility=scores.get("feasibility"),
            importance=scores.get("importance"),
            evidence_support=scores.get("evidence_support"),
            validation_clarity=scores.get("validation_clarity"),
            differentiation=scores.get("differentiation"),
            data_availability=scores.get("data_availability"),
            skill_leverage=scores.get("skill_leverage"),
            user_alignment=scores.get("user_alignment"),
            prior_art_risk=scores.get("prior_art_risk"),
            safety_risk=scores.get("safety_risk"),
            cost_risk=scores.get("cost_risk"),
            overall_value=scores.get("overall_value"),
            scoring_rationale=rationale,
        )
        self.db.add(score)

        # Update idea's overall score and classification
        idea = await self.get_idea(idea_id)
        if idea and scores.get("overall_value") is not None:
            idea.overall_score = scores["overall_value"]
            # Auto-classify based on score
            score_val = scores["overall_value"]
            if score_val >= 8.0:
                idea.classification = "high_value"
            elif score_val >= 6.5:
                idea.classification = "promising"
            elif score_val >= 5.0:
                idea.classification = "incremental"
            elif score_val >= 3.5:
                idea.classification = "weak"
            else:
                idea.classification = "reject"

        await self.db.flush()
        return score

    async def add_decision(
        self,
        idea_id: str,
        decision: str,
        reason: str | None = None,
        run_id: str | None = None,
    ) -> IdeaDecision:
        """Add a decision record to an idea."""
        decision_record = IdeaDecision(
            id=str(uuid4()),
            idea_id=idea_id,
            run_id=run_id,
            decision=decision,
            reason=reason,
        )
        self.db.add(decision_record)

        # Update idea status based on decision
        idea = await self.get_idea(idea_id)
        if idea:
            if decision == "reject":
                idea.status = "rejected"
            elif decision == "promote":
                idea.status = "promoted"
            elif decision == "archive":
                idea.status = "archived"

        await self.db.flush()
        return decision_record

    async def get_idea_versions(self, idea_id: str) -> list[IdeaVersion]:
        """Get version history for an idea."""
        result = await self.db.execute(
            select(IdeaVersion)
            .where(IdeaVersion.idea_id == idea_id)
            .order_by(IdeaVersion.version_number)
        )
        return list(result.scalars().all())

    async def get_idea_scores(self, idea_id: str) -> list[IdeaScore]:
        """Get score history for an idea."""
        result = await self.db.execute(
            select(IdeaScore)
            .where(IdeaScore.idea_id == idea_id)
            .order_by(IdeaScore.created_at)
        )
        return list(result.scalars().all())

    async def get_idea_decisions(self, idea_id: str) -> list[IdeaDecision]:
        """Get decision history for an idea."""
        result = await self.db.execute(
            select(IdeaDecision)
            .where(IdeaDecision.idea_id == idea_id)
            .order_by(IdeaDecision.created_at)
        )
        return list(result.scalars().all())

    async def get_linked_papers(self, idea_id: str) -> list[Paper]:
        """Get papers linked to an idea through research runs."""
        from ..models.research_run import ResearchRun

        # Get runs for this idea
        runs_result = await self.db.execute(
            select(ResearchRun.id).where(ResearchRun.idea_id == idea_id)
        )
        run_ids = [r[0] for r in runs_result.all()]

        if not run_ids:
            return []

        # Get papers from project (simplified - in real impl, link through runs)
        idea = await self.get_idea(idea_id)
        if not idea:
            return []

        papers_result = await self.db.execute(
            select(Paper).where(Paper.project_id == idea.project_id).limit(50)
        )
        return list(papers_result.scalars().all())

    async def get_linked_hypotheses(self, idea_id: str) -> list[Hypothesis]:
        """Get hypotheses linked to an idea."""
        result = await self.db.execute(
            select(Hypothesis).where(Hypothesis.idea_id == idea_id)
        )
        return list(result.scalars().all())

    async def get_linked_questions(self, idea_id: str) -> list[ResearchQuestion]:
        """Get research questions linked to an idea."""
        result = await self.db.execute(
            select(ResearchQuestion).where(ResearchQuestion.idea_id == idea_id)
        )
        return list(result.scalars().all())

    async def list_ideas(
        self,
        project_id: str,
        status: str | None = None,
        classification: str | None = None,
        origin: str | None = None,
        min_score: float | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[Idea]:
        """List ideas with comprehensive filters."""
        query = select(Idea).where(Idea.project_id == project_id)

        if status:
            query = query.where(Idea.status == status)
        if classification:
            query = query.where(Idea.classification == classification)
        if origin:
            query = query.where(Idea.origin == origin)
        if min_score is not None:
            query = query.where(Idea.overall_score >= min_score)

        offset = (page - 1) * per_page
        query = query.order_by(Idea.created_at.desc()).offset(offset).limit(per_page)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_ideas(
        self,
        project_id: str,
        search_text: str,
    ) -> list[Idea]:
        """Search ideas by text content."""
        search_pattern = f"%{search_text}%"

        result = await self.db.execute(
            select(Idea).where(
                Idea.project_id == project_id,
                or_(
                    Idea.initial_text.ilike(search_pattern),
                    Idea.current_text.ilike(search_pattern),
                )
            )
        )
        return list(result.scalars().all())

    async def get_idea_statistics(self, project_id: str) -> dict[str, Any]:
        """Get comprehensive idea statistics."""
        # Total ideas
        total_result = await self.db.execute(
            select(func.count(Idea.id)).where(Idea.project_id == project_id)
        )
        total = total_result.scalar() or 0

        # By status
        status_result = await self.db.execute(
            select(Idea.status, func.count(Idea.id))
            .where(Idea.project_id == project_id)
            .group_by(Idea.status)
        )
        by_status = {row[0] or "unknown": row[1] for row in status_result.all()}

        # By classification
        class_result = await self.db.execute(
            select(Idea.classification, func.count(Idea.id))
            .where(Idea.project_id == project_id)
            .group_by(Idea.classification)
        )
        by_classification = {row[0] or "unknown": row[1] for row in class_result.all()}

        # By origin
        origin_result = await self.db.execute(
            select(Idea.origin, func.count(Idea.id))
            .where(Idea.project_id == project_id)
            .group_by(Idea.origin)
        )
        by_origin = {row[0] or "unknown": row[1] for row in origin_result.all()}

        # Average score
        avg_result = await self.db.execute(
            select(func.avg(Idea.overall_score))
            .where(Idea.project_id == project_id)
            .where(Idea.overall_score.isnot(None))
        )
        avg_score = avg_result.scalar() or 0

        return {
            "total_ideas": total,
            "by_status": by_status,
            "by_classification": by_classification,
            "by_origin": by_origin,
            "avg_score": round(avg_score, 2),
        }

    async def revive_rejected_idea(
        self,
        idea_id: str,
        reason: str = "New evidence supports reconsideration",
    ) -> Idea | None:
        """Revive a rejected idea."""
        idea = await self.get_idea(idea_id)
        if not idea or idea.status != "rejected":
            return None

        # Update status
        idea.status = "active"

        # Add decision record
        await self.add_decision(
            idea_id=idea_id,
            decision="revive",
            reason=reason,
        )

        return idea

    async def get_idea_full_context(self, idea_id: str) -> dict[str, Any] | None:
        """Get complete context for an idea."""
        idea = await self.get_idea(idea_id)
        if not idea:
            return None

        versions = await self.get_idea_versions(idea_id)
        scores = await self.get_idea_scores(idea_id)
        decisions = await self.get_idea_decisions(idea_id)
        papers = await self.get_linked_papers(idea_id)
        hypotheses = await self.get_linked_hypotheses(idea_id)
        questions = await self.get_linked_questions(idea_id)

        return {
            "idea": idea,
            "versions": versions,
            "scores": scores,
            "decisions": decisions,
            "linked_papers": papers,
            "linked_hypotheses": hypotheses,
            "linked_questions": questions,
            "version_count": len(versions),
            "score_count": len(scores),
            "decision_count": len(decisions),
        }
