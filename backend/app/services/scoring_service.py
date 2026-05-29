"""Idea scoring service for storing and managing scores."""

from uuid import uuid4
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.idea import Idea, IdeaScore as IdeaScoreModel, IdeaClassification
from ..engine.scoring import IdeaScore, ScoringResult


class IdeaScoringService:
    """Service for storing and managing idea scores."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_score(
        self,
        score: IdeaScore,
    ) -> IdeaScoreModel:
        """Store an idea score in the database."""
        score_record = IdeaScoreModel(
            id=str(uuid4()),
            idea_id=score.idea_id,
            novelty=score.novelty,
            feasibility=score.feasibility,
            importance=score.importance,
            evidence_support=score.evidence_support,
            validation_clarity=score.validation_clarity,
            differentiation=score.differentiation,
            data_availability=score.data_availability,
            skill_leverage=score.skill_leverage,
            user_alignment=score.user_alignment,
            prior_art_risk=score.prior_art_risk,
            safety_risk=score.safety_risk,
            cost_risk=score.cost_risk,
            overall_value=score.overall_value,
            scoring_rationale=score.rationale,
        )
        self.db.add(score_record)

        # Update idea with score and classification
        idea_result = await self.db.execute(
            select(Idea).where(Idea.id == score.idea_id)
        )
        idea = idea_result.scalar_one_or_none()
        if idea:
            idea.overall_score = score.overall_value
            idea.classification = score.classification

        # Store classification
        classification_record = IdeaClassification(
            id=str(uuid4()),
            idea_id=score.idea_id,
            classification=score.classification,
            score=score.overall_value,
            reason=score.rationale,
        )
        self.db.add(classification_record)

        await self.db.flush()
        return score_record

    async def store_scores(
        self,
        result: ScoringResult,
    ) -> list[IdeaScoreModel]:
        """Store multiple idea scores."""
        stored_scores = []
        for score in result.scores:
            stored_score = await self.store_score(score)
            stored_scores.append(stored_score)
        return stored_scores

    async def get_idea_scores(
        self,
        idea_id: str,
    ) -> list[IdeaScoreModel]:
        """Get all scores for an idea."""
        result = await self.db.execute(
            select(IdeaScoreModel)
            .where(IdeaScoreModel.idea_id == idea_id)
            .order_by(IdeaScoreModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_latest_score(
        self,
        idea_id: str,
    ) -> IdeaScoreModel | None:
        """Get the latest score for an idea."""
        scores = await self.get_idea_scores(idea_id)
        return scores[0] if scores else None

    async def get_project_scores(
        self,
        project_id: str,
        classification: str | None = None,
        min_score: float | None = None,
    ) -> list[IdeaScoreModel]:
        """Get scores for all ideas in a project."""
        query = (
            select(IdeaScoreModel)
            .join(Idea, IdeaScoreModel.idea_id == Idea.id)
            .where(Idea.project_id == project_id)
        )

        if min_score is not None:
            query = query.where(IdeaScoreModel.overall_value >= min_score)

        query = query.order_by(IdeaScoreModel.overall_value.desc())

        result = await self.db.execute(query)
        scores = list(result.scalars().all())

        # Filter by classification if specified
        if classification:
            scores = [s for s in scores if self._get_classification(s.overall_value) == classification]

        return scores

    def _get_classification(self, score: float) -> str:
        """Get classification from score."""
        if score >= 8.0:
            return "high_value"
        elif score >= 6.5:
            return "promising"
        elif score >= 5.0:
            return "incremental"
        elif score >= 3.5:
            return "weak"
        else:
            return "reject"

    async def get_score_statistics(
        self,
        project_id: str,
    ) -> dict[str, Any]:
        """Get statistics about scores in a project."""
        from sqlalchemy import func

        # Total scores
        total_result = await self.db.execute(
            select(func.count(IdeaScoreModel.id))
            .join(Idea, IdeaScoreModel.idea_id == Idea.id)
            .where(Idea.project_id == project_id)
        )
        total = total_result.scalar() or 0

        # Average score
        avg_result = await self.db.execute(
            select(func.avg(IdeaScoreModel.overall_value))
            .join(Idea, IdeaScoreModel.idea_id == Idea.id)
            .where(Idea.project_id == project_id)
        )
        avg_score = avg_result.scalar() or 0

        # Max and min scores
        max_result = await self.db.execute(
            select(func.max(IdeaScoreModel.overall_value))
            .join(Idea, IdeaScoreModel.idea_id == Idea.id)
            .where(Idea.project_id == project_id)
        )
        max_score = max_result.scalar() or 0

        min_result = await self.db.execute(
            select(func.min(IdeaScoreModel.overall_value))
            .join(Idea, IdeaScoreModel.idea_id == Idea.id)
            .where(Idea.project_id == project_id)
        )
        min_score = min_result.scalar() or 0

        return {
            "total_scored": total,
            "avg_score": round(avg_score, 2),
            "max_score": round(max_score, 2),
            "min_score": round(min_score, 2),
        }
