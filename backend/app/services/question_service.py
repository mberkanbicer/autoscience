"""Research question service for storing and managing questions."""

from uuid import uuid4
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.research_question import ResearchQuestion as ResearchQuestionModel
from ..engine.question_generation import ResearchQuestion, QuestionGenerationResult


class ResearchQuestionService:
    """Service for storing and managing research questions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_questions(
        self,
        project_id: str,
        result: QuestionGenerationResult,
        run_id: str | None = None,
        idea_id: str | None = None,
    ) -> list[ResearchQuestionModel]:
        """Store generated questions in the database."""
        stored_questions = []

        for question in result.questions:
            question_record = ResearchQuestionModel(
                id=question.id,
                project_id=project_id,
                run_id=run_id,
                idea_id=idea_id,
                question=question.question,
                source_conflicts=question.source_conflicts,
                source_gaps=question.source_gaps,
                rank=question.overall_score,
                status=question.status,
            )
            self.db.add(question_record)
            stored_questions.append(question_record)

        # Store rejected questions with reasons
        for question in result.rejected_questions:
            question_record = ResearchQuestionModel(
                id=question.id,
                project_id=project_id,
                run_id=run_id,
                idea_id=idea_id,
                question=question.question,
                source_conflicts=question.source_conflicts,
                source_gaps=question.source_gaps,
                rank=question.overall_score,
                status="rejected",
                rejection_reason=question.rejection_reason,
            )
            self.db.add(question_record)

        await self.db.flush()
        return stored_questions

    async def get_project_questions(
        self,
        project_id: str,
        status: str | None = None,
        min_rank: float | None = None,
    ) -> list[ResearchQuestionModel]:
        """Get all questions for a project."""
        query = select(ResearchQuestionModel).where(
            ResearchQuestionModel.project_id == project_id
        )

        if status:
            query = query.where(ResearchQuestionModel.status == status)
        if min_rank is not None:
            query = query.where(ResearchQuestionModel.rank >= min_rank)

        query = query.order_by(ResearchQuestionModel.rank.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_question(self, question_id: str) -> ResearchQuestionModel | None:
        """Get a question by ID."""
        result = await self.db.execute(
            select(ResearchQuestionModel).where(ResearchQuestionModel.id == question_id)
        )
        return result.scalar_one_or_none()

    async def update_question_status(
        self,
        question_id: str,
        status: str,
        rejection_reason: str | None = None,
    ) -> ResearchQuestionModel | None:
        """Update question status."""
        question = await self.get_question(question_id)
        if not question:
            return None

        question.status = status
        if rejection_reason:
            question.rejection_reason = rejection_reason

        await self.db.flush()
        return question

    async def reject_question(
        self,
        question_id: str,
        reason: str,
    ) -> ResearchQuestionModel | None:
        """Reject a question with reason."""
        return await self.update_question_status(
            question_id, "rejected", rejection_reason=reason
        )

    async def promote_to_hypothesis(
        self,
        question_id: str,
    ) -> ResearchQuestionModel | None:
        """Mark question as hypothesis created."""
        return await self.update_question_status(question_id, "hypothesis_created")

    async def delete_question(self, question_id: str) -> bool:
        """Delete a question."""
        question = await self.get_question(question_id)
        if not question:
            return False

        await self.db.delete(question)
        return True

    async def get_question_statistics(self, project_id: str) -> dict[str, Any]:
        """Get statistics about questions in a project."""
        from sqlalchemy import func

        # Total questions
        total_result = await self.db.execute(
            select(func.count(ResearchQuestionModel.id)).where(
                ResearchQuestionModel.project_id == project_id
            )
        )
        total = total_result.scalar() or 0

        # By status
        status_result = await self.db.execute(
            select(ResearchQuestionModel.status, func.count(ResearchQuestionModel.id))
            .where(ResearchQuestionModel.project_id == project_id)
            .group_by(ResearchQuestionModel.status)
        )
        by_status = {row[0] or "unknown": row[1] for row in status_result.all()}

        # Average rank
        avg_rank_result = await self.db.execute(
            select(func.avg(ResearchQuestionModel.rank)).where(
                ResearchQuestionModel.project_id == project_id,
                ResearchQuestionModel.status == "selected",
            )
        )
        avg_rank = avg_rank_result.scalar() or 0

        return {
            "total_questions": total,
            "by_status": by_status,
            "avg_rank_selected": round(avg_rank, 2),
        }

    async def search_questions(
        self,
        project_id: str,
        search_text: str,
    ) -> list[ResearchQuestionModel]:
        """Search questions by text."""
        search_pattern = f"%{search_text}%"

        result = await self.db.execute(
            select(ResearchQuestionModel).where(
                ResearchQuestionModel.project_id == project_id,
                ResearchQuestionModel.question.ilike(search_pattern),
            )
        )
        return list(result.scalars().all())
