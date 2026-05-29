"""Hypothesis service for storing and managing hypotheses."""

from uuid import uuid4
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.research_question import Hypothesis as HypothesisModel
from ..engine.hypothesis_generation import Hypothesis, HypothesisGenerationResult


class HypothesisService:
    """Service for storing and managing hypotheses."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_hypotheses(
        self,
        project_id: str,
        result: HypothesisGenerationResult,
        idea_id: str | None = None,
    ) -> list[HypothesisModel]:
        """Store generated hypotheses in the database."""
        stored_hypotheses = []

        for hypothesis in result.hypotheses:
            hypothesis_record = HypothesisModel(
                id=hypothesis.id,
                project_id=project_id,
                idea_id=idea_id,
                question_id=hypothesis.question_id,
                statement=hypothesis.statement,
                independent_variable=hypothesis.independent_variable,
                dependent_variable=hypothesis.dependent_variable,
                context=hypothesis.context,
                expected_direction=hypothesis.expected_direction,
                baseline=hypothesis.baseline,
                metric=hypothesis.metric,
                dataset_requirement=hypothesis.dataset_requirement,
                failure_condition=hypothesis.failure_condition,
                confidence=hypothesis.confidence,
                version=hypothesis.version,
                status=hypothesis.status,
            )
            self.db.add(hypothesis_record)
            stored_hypotheses.append(hypothesis_record)

        await self.db.flush()
        return stored_hypotheses

    async def get_project_hypotheses(
        self,
        project_id: str,
        status: str | None = None,
        min_confidence: float | None = None,
    ) -> list[HypothesisModel]:
        """Get all hypotheses for a project."""
        query = select(HypothesisModel).where(
            HypothesisModel.project_id == project_id
        )

        if status:
            query = query.where(HypothesisModel.status == status)
        if min_confidence is not None:
            query = query.where(HypothesisModel.confidence >= min_confidence)

        query = query.order_by(HypothesisModel.confidence.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_hypothesis(self, hypothesis_id: str) -> HypothesisModel | None:
        """Get a hypothesis by ID."""
        result = await self.db.execute(
            select(HypothesisModel).where(HypothesisModel.id == hypothesis_id)
        )
        return result.scalar_one_or_none()

    async def update_hypothesis(
        self,
        hypothesis_id: str,
        statement: str | None = None,
        confidence: float | None = None,
        status: str | None = None,
    ) -> HypothesisModel | None:
        """Update a hypothesis."""
        hypothesis = await self.get_hypothesis(hypothesis_id)
        if not hypothesis:
            return None

        if statement is not None:
            hypothesis.statement = statement
        if confidence is not None:
            hypothesis.confidence = confidence
        if status is not None:
            hypothesis.status = status

        await self.db.flush()
        return hypothesis

    async def create_version(
        self,
        hypothesis_id: str,
        statement: str,
        confidence: float | None = None,
    ) -> HypothesisModel | None:
        """Create a new version of a hypothesis."""
        hypothesis = await self.get_hypothesis(hypothesis_id)
        if not hypothesis:
            return None

        # Create new version
        new_hypothesis = HypothesisModel(
            id=str(uuid4()),
            project_id=hypothesis.project_id,
            idea_id=hypothesis.idea_id,
            question_id=hypothesis.question_id,
            statement=statement,
            independent_variable=hypothesis.independent_variable,
            dependent_variable=hypothesis.dependent_variable,
            context=hypothesis.context,
            expected_direction=hypothesis.expected_direction,
            baseline=hypothesis.baseline,
            metric=hypothesis.metric,
            dataset_requirement=hypothesis.dataset_requirement,
            failure_condition=hypothesis.failure_condition,
            confidence=confidence or hypothesis.confidence,
            version=hypothesis.version + 1,
            status=hypothesis.status,
        )
        self.db.add(new_hypothesis)
        await self.db.flush()

        return new_hypothesis

    async def delete_hypothesis(self, hypothesis_id: str) -> bool:
        """Delete a hypothesis."""
        hypothesis = await self.get_hypothesis(hypothesis_id)
        if not hypothesis:
            return False

        await self.db.delete(hypothesis)
        return True

    async def get_hypothesis_statistics(self, project_id: str) -> dict[str, Any]:
        """Get statistics about hypotheses in a project."""
        from sqlalchemy import func

        # Total hypotheses
        total_result = await self.db.execute(
            select(func.count(HypothesisModel.id)).where(
                HypothesisModel.project_id == project_id
            )
        )
        total = total_result.scalar() or 0

        # By status
        status_result = await self.db.execute(
            select(HypothesisModel.status, func.count(HypothesisModel.id))
            .where(HypothesisModel.project_id == project_id)
            .group_by(HypothesisModel.status)
        )
        by_status = {row[0] or "unknown": row[1] for row in status_result.all()}

        # Average confidence
        avg_conf_result = await self.db.execute(
            select(func.avg(HypothesisModel.confidence)).where(
                HypothesisModel.project_id == project_id,
                HypothesisModel.status == "validated",
            )
        )
        avg_confidence = avg_conf_result.scalar() or 0

        return {
            "total_hypotheses": total,
            "by_status": by_status,
            "avg_confidence_validated": round(avg_confidence, 2),
        }

    async def search_hypotheses(
        self,
        project_id: str,
        search_text: str,
    ) -> list[HypothesisModel]:
        """Search hypotheses by statement."""
        search_pattern = f"%{search_text}%"

        result = await self.db.execute(
            select(HypothesisModel).where(
                HypothesisModel.project_id == project_id,
                HypothesisModel.statement.ilike(search_pattern),
            )
        )
        return list(result.scalars().all())
