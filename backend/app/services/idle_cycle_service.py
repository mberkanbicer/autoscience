"""Idle cycle service for storing and managing idle cycles."""

from uuid import uuid4
from typing import Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..models.research_run import IdleCycle
from ..engine.idle_cognition import IdleCycleResult


class IdleCycleService:
    """Service for storing and managing idle cycles."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_cycle(
        self,
        project_id: str,
        result: IdleCycleResult,
        run_id: str | None = None,
    ) -> IdleCycle:
        """Store an idle cycle result."""
        cycle = IdleCycle(
            id=result.cycle_id,
            project_id=project_id,
            run_id=run_id,
            idle_mode=result.idle_mode,
            trigger_reason="Autonomous idle cognition",
            ideas_generated=result.ideas_generated,
            questions_generated=result.questions_generated,
            hypotheses_generated=result.hypotheses_generated,
            skills_created=result.skills_created,
            duration_seconds=int(result.duration_seconds),
            cost_usd=result.cost_usd,
            started_at=datetime.now(),
            completed_at=datetime.now(),
        )
        self.db.add(cycle)
        await self.db.flush()
        return cycle

    async def get_project_cycles(
        self,
        project_id: str,
        idle_mode: str | None = None,
        limit: int = 50,
    ) -> list[IdleCycle]:
        """Get idle cycles for a project."""
        query = select(IdleCycle).where(IdleCycle.project_id == project_id)

        if idle_mode:
            query = query.where(IdleCycle.idle_mode == idle_mode)

        query = query.order_by(IdleCycle.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_cycle(self, cycle_id: str) -> IdleCycle | None:
        """Get a cycle by ID."""
        result = await self.db.execute(
            select(IdleCycle).where(IdleCycle.id == cycle_id)
        )
        return result.scalar_one_or_none()

    async def get_cycle_statistics(
        self,
        project_id: str,
    ) -> dict[str, Any]:
        """Get statistics about idle cycles."""
        from sqlalchemy import func

        # Total cycles
        total_result = await self.db.execute(
            select(func.count(IdleCycle.id)).where(
                IdleCycle.project_id == project_id
            )
        )
        total = total_result.scalar() or 0

        # By mode
        mode_result = await self.db.execute(
            select(IdleCycle.idle_mode, func.count(IdleCycle.id))
            .where(IdleCycle.project_id == project_id)
            .group_by(IdleCycle.idle_mode)
        )
        by_mode = {row[0] or "unknown": row[1] for row in mode_result.all()}

        # Total outputs
        outputs_result = await self.db.execute(
            select(
                func.sum(IdleCycle.ideas_generated).label("ideas"),
                func.sum(IdleCycle.questions_generated).label("questions"),
                func.sum(IdleCycle.hypotheses_generated).label("hypotheses"),
                func.sum(IdleCycle.skills_created).label("skills"),
            ).where(IdleCycle.project_id == project_id)
        )
        outputs = outputs_result.one()

        # Duration stats
        duration_result = await self.db.execute(
            select(
                func.avg(IdleCycle.duration_seconds).label("avg_duration"),
                func.sum(IdleCycle.duration_seconds).label("total_duration"),
            ).where(IdleCycle.project_id == project_id)
        )
        duration_stats = duration_result.one()

        return {
            "total_cycles": total,
            "by_mode": by_mode,
            "total_ideas": outputs.ideas or 0,
            "total_questions": outputs.questions or 0,
            "total_hypotheses": outputs.hypotheses or 0,
            "total_skills": outputs.skills or 0,
            "avg_duration_seconds": round(duration_stats.avg_duration or 0, 1),
            "total_duration_seconds": duration_stats.total_duration or 0,
        }

    async def get_recent_cycles(
        self,
        project_id: str,
        days: int = 7,
    ) -> list[IdleCycle]:
        """Get recent cycles within specified days."""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)

        result = await self.db.execute(
            select(IdleCycle)
            .where(
                IdleCycle.project_id == project_id,
                IdleCycle.created_at >= cutoff,
            )
            .order_by(IdleCycle.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_cycle(self, cycle_id: str) -> bool:
        """Delete a cycle."""
        cycle = await self.get_cycle(cycle_id)
        if not cycle:
            return False

        await self.db.delete(cycle)
        return True
