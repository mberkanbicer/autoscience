"""Validation plan service for storing and managing plans."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.validation_planning import ValidationPlan, ValidationPlanResult
from app.models.research_question import ValidationPlan as ValidationPlanModel


class ValidationPlanService:
    """Service for storing and managing validation plans."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_plan(
        self,
        plan: ValidationPlan,
    ) -> ValidationPlanModel:
        """Store a validation plan in the database."""
        # Check if plan already exists for this hypothesis
        existing = await self.get_plan_for_hypothesis(plan.hypothesis_id)

        if existing:
            # Update existing plan
            return await self._update_plan(existing, plan)

        # Create new plan
        plan_record = ValidationPlanModel(
            id=plan.id,
            hypothesis_id=plan.hypothesis_id,
            dataset_candidates=[
                {
                    "name": d.name,
                    "source": d.source,
                    "url": d.url,
                    "description": d.description,
                    "size": d.size,
                    "format": d.format,
                    "relevance_score": d.relevance_score,
                }
                for d in plan.dataset_candidates
            ],
            benchmark_candidates=plan.benchmark_candidates,
            baselines=plan.baselines,
            metrics=plan.metrics,
            experimental_design=plan.experimental_design,
            statistical_tests=plan.statistical_tests,
            simulation_option=plan.simulation_option,
            expected_artifacts=plan.expected_artifacts,
            difficulty_estimate=plan.difficulty_estimate,
            cost_estimate=plan.cost_estimate,
            feasibility_score=plan.feasibility_score,
        )
        self.db.add(plan_record)
        await self.db.flush()

        return plan_record

    async def _update_plan(
        self,
        existing: ValidationPlanModel,
        plan: ValidationPlan,
    ) -> ValidationPlanModel:
        """Update an existing validation plan."""
        # Update with new data if more complete
        if plan.feasibility_score > (existing.feasibility_score or 0):
            existing.dataset_candidates = [
                {
                    "name": d.name,
                    "source": d.source,
                    "url": d.url,
                    "description": d.description,
                    "size": d.size,
                    "format": d.format,
                    "relevance_score": d.relevance_score,
                }
                for d in plan.dataset_candidates
            ] or existing.dataset_candidates
            existing.baselines = plan.baselines or existing.baselines
            existing.metrics = plan.metrics or existing.metrics
            existing.experimental_design = plan.experimental_design or existing.experimental_design
            existing.statistical_tests = plan.statistical_tests or existing.statistical_tests
            existing.difficulty_estimate = plan.difficulty_estimate
            existing.cost_estimate = plan.cost_estimate
            existing.feasibility_score = plan.feasibility_score

        await self.db.flush()
        return existing

    async def store_plans(
        self,
        result: ValidationPlanResult,
    ) -> list[ValidationPlanModel]:
        """Store multiple validation plans."""
        stored_plans = []
        for plan in result.plans:
            stored_plan = await self.store_plan(plan)
            stored_plans.append(stored_plan)
        return stored_plans

    async def get_plan(self, plan_id: str) -> ValidationPlanModel | None:
        """Get a validation plan by ID."""
        result = await self.db.execute(
            select(ValidationPlanModel).where(ValidationPlanModel.id == plan_id),
        )
        return result.scalar_one_or_none()

    async def get_plan_for_hypothesis(
        self,
        hypothesis_id: str,
    ) -> ValidationPlanModel | None:
        """Get validation plan for a hypothesis."""
        result = await self.db.execute(
            select(ValidationPlanModel).where(
                ValidationPlanModel.hypothesis_id == hypothesis_id,
            ),
        )
        return result.scalar_one_or_none()

    async def get_project_plans(
        self,
        project_id: str,
    ) -> list[ValidationPlanModel]:
        """Get all validation plans for a project."""
        from app.models.research_question import Hypothesis

        result = await self.db.execute(
            select(ValidationPlanModel)
            .join(Hypothesis, ValidationPlanModel.hypothesis_id == Hypothesis.id)
            .where(Hypothesis.project_id == project_id),
        )
        return list(result.scalars().all())

    async def update_plan(
        self,
        plan_id: str,
        experimental_design: str | None = None,
        metrics: list[str] | None = None,
        feasibility_score: float | None = None,
    ) -> ValidationPlanModel | None:
        """Update a validation plan."""
        plan = await self.get_plan(plan_id)
        if not plan:
            return None

        if experimental_design is not None:
            plan.experimental_design = experimental_design
        if metrics is not None:
            plan.metrics = metrics
        if feasibility_score is not None:
            plan.feasibility_score = feasibility_score

        await self.db.flush()
        return plan

    async def delete_plan(self, plan_id: str) -> bool:
        """Delete a validation plan."""
        plan = await self.get_plan(plan_id)
        if not plan:
            return False

        await self.db.delete(plan)
        return True

    async def get_plan_statistics(
        self,
        project_id: str,
    ) -> dict[str, Any]:
        """Get statistics about validation plans."""
        plans = await self.get_project_plans(project_id)

        if not plans:
            return {
                "total_plans": 0,
                "avg_feasibility": 0,
                "avg_cost": 0,
                "avg_difficulty": 0,
            }

        avg_feasibility = sum(p.feasibility_score or 0 for p in plans) / len(plans)
        avg_cost = sum(p.cost_estimate or 0 for p in plans) / len(plans)
        avg_difficulty = sum(p.difficulty_estimate or 0 for p in plans) / len(plans)

        return {
            "total_plans": len(plans),
            "avg_feasibility": round(avg_feasibility, 2),
            "avg_cost": round(avg_cost, 2),
            "avg_difficulty": round(avg_difficulty, 2),
        }
