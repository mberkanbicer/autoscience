"""Research question and hypothesis service layer."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.research_question import ResearchQuestion, Hypothesis, ValidationPlan
from ..schemas.research_question import (
    ResearchQuestionCreate,
    HypothesisCreate,
    HypothesisUpdate,
    ValidationPlanCreate,
)


class ResearchQuestionService:
    """Service for research question operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_questions(
        self,
        project_id: str,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[ResearchQuestion]:
        """List research questions for a project."""
        query = select(ResearchQuestion).where(ResearchQuestion.project_id == project_id)

        if status:
            query = query.where(ResearchQuestion.status == status)

        offset = (page - 1) * per_page
        query = query.order_by(ResearchQuestion.rank.desc().nullslast()).offset(offset).limit(per_page)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_question(
        self,
        project_id: str,
        data: ResearchQuestionCreate,
        run_id: str | None = None,
    ) -> ResearchQuestion:
        """Create a new research question."""
        question = ResearchQuestion(
            id=str(uuid4()),
            project_id=project_id,
            idea_id=data.idea_id,
            run_id=run_id,
            question=data.question,
            source_conflicts=data.source_conflicts,
            source_gaps=data.source_gaps,
            status="generated",
        )
        self.db.add(question)
        await self.db.flush()
        return question

    async def get_question(self, question_id: str) -> ResearchQuestion | None:
        """Get a research question by ID."""
        result = await self.db.execute(
            select(ResearchQuestion).where(ResearchQuestion.id == question_id)
        )
        return result.scalar_one_or_none()

    async def reject_question(
        self,
        question_id: str,
        reason: str,
    ) -> ResearchQuestion | None:
        """Reject a research question."""
        question = await self.get_question(question_id)
        if not question:
            return None

        question.status = "rejected"
        question.rejection_reason = reason
        await self.db.flush()
        return question


class HypothesisService:
    """Service for hypothesis operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_hypotheses(
        self,
        project_id: str,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[Hypothesis]:
        """List hypotheses for a project."""
        query = select(Hypothesis).where(Hypothesis.project_id == project_id)

        if status:
            query = query.where(Hypothesis.status == status)

        offset = (page - 1) * per_page
        query = query.order_by(Hypothesis.created_at.desc()).offset(offset).limit(per_page)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_hypothesis(
        self,
        project_id: str,
        data: HypothesisCreate,
    ) -> Hypothesis:
        """Create a new hypothesis."""
        hypothesis = Hypothesis(
            id=str(uuid4()),
            project_id=project_id,
            idea_id=data.idea_id,
            question_id=data.question_id,
            statement=data.statement,
            independent_variable=data.independent_variable,
            dependent_variable=data.dependent_variable,
            context=data.context,
            expected_direction=data.expected_direction,
            baseline=data.baseline,
            metric=data.metric,
            dataset_requirement=data.dataset_requirement,
            failure_condition=data.failure_condition,
            version=1,
            status="draft",
        )
        self.db.add(hypothesis)

        # Update question status if linked
        if data.question_id:
            question = await self.db.execute(
                select(ResearchQuestion).where(ResearchQuestion.id == data.question_id)
            )
            q = question.scalar_one_or_none()
            if q:
                q.status = "hypothesis_created"

        await self.db.flush()
        return hypothesis

    async def get_hypothesis(self, hypothesis_id: str) -> Hypothesis | None:
        """Get a hypothesis by ID."""
        result = await self.db.execute(
            select(Hypothesis).where(Hypothesis.id == hypothesis_id)
        )
        return result.scalar_one_or_none()

    async def update_hypothesis(
        self,
        hypothesis_id: str,
        data: HypothesisUpdate,
    ) -> Hypothesis | None:
        """Update a hypothesis."""
        hypothesis = await self.get_hypothesis(hypothesis_id)
        if not hypothesis:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(hypothesis, field, value)

        await self.db.flush()
        return hypothesis

    async def get_validation_plan(self, hypothesis_id: str) -> ValidationPlan | None:
        """Get validation plan for a hypothesis."""
        result = await self.db.execute(
            select(ValidationPlan).where(ValidationPlan.hypothesis_id == hypothesis_id)
        )
        return result.scalar_one_or_none()

    async def create_validation_plan(
        self,
        data: ValidationPlanCreate,
    ) -> ValidationPlan:
        """Create or update a validation plan."""
        existing = await self.get_validation_plan(data.hypothesis_id)

        if existing:
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field != "hypothesis_id":
                    setattr(existing, field, value)
            await self.db.flush()
            return existing

        plan = ValidationPlan(
            id=str(uuid4()),
            hypothesis_id=data.hypothesis_id,
            dataset_candidates=data.dataset_candidates,
            benchmark_candidates=data.benchmark_candidates,
            baselines=data.baselines,
            metrics=data.metrics,
            experimental_design=data.experimental_design,
            statistical_tests=data.statistical_tests,
            simulation_option=data.simulation_option,
            expected_artifacts=data.expected_artifacts,
            difficulty_estimate=data.difficulty_estimate,
            cost_estimate=data.cost_estimate,
            feasibility_score=data.feasibility_score,
        )
        self.db.add(plan)
        await self.db.flush()
        return plan
