"""Skill memory system for learning reusable research methods."""

from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill, SkillEvaluation, SkillUsage, SkillVersion


class SkillMemoryService:
    """Service for skill memory and learning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # Skill lifecycle states
    LIFECYCLE = ["candidate", "tested", "active", "revised", "deprecated", "retired"]

    async def create_skill(
        self,
        name: str,
        skill_type: str,
        purpose: str,
        procedure: list[str],
        inputs: list[str] | None = None,
        outputs: list[str] | None = None,
        trigger_conditions: list[str] | None = None,
        project_id: str | None = None,
    ) -> Skill:
        """Create a new skill."""
        skill = Skill(
            id=str(uuid4()),
            project_id=project_id,
            name=name,
            skill_type=skill_type,
            purpose=purpose,
            procedure=procedure,
            inputs=inputs or [],
            outputs=outputs or [],
            trigger_conditions=trigger_conditions or [],
            status="candidate",
            version="1.0",
        )
        self.db.add(skill)

        # Create initial version
        version = SkillVersion(
            id=str(uuid4()),
            skill_id=skill.id,
            version="1.0",
            changes="Initial version",
            procedure=procedure,
        )
        self.db.add(version)

        await self.db.flush()
        return skill

    async def get_skill(self, skill_id: str) -> Skill | None:
        """Get a skill by ID."""
        result = await self.db.execute(select(Skill).where(Skill.id == skill_id))
        return result.scalar_one_or_none()

    async def update_skill(
        self,
        skill_id: str,
        name: str | None = None,
        purpose: str | None = None,
        procedure: list[str] | None = None,
        inputs: list[str] | None = None,
        outputs: list[str] | None = None,
        trigger_conditions: list[str] | None = None,
    ) -> Skill | None:
        """Update a skill and create new version."""
        skill = await self.get_skill(skill_id)
        if not skill:
            return None

        # Increment version
        major, minor = skill.version.split(".")
        new_version_str = f"{major}.{int(minor) + 1}"

        # Update fields
        if name is not None:
            skill.name = name
        if purpose is not None:
            skill.purpose = purpose
        if procedure is not None:
            skill.procedure = procedure
        if inputs is not None:
            skill.inputs = inputs
        if outputs is not None:
            skill.outputs = outputs
        if trigger_conditions is not None:
            skill.trigger_conditions = trigger_conditions

        skill.version = new_version_str

        # Create version record
        version = SkillVersion(
            id=str(uuid4()),
            skill_id=skill_id,
            version=new_version_str,
            changes="Updated via API",
            procedure=procedure or skill.procedure,
        )
        self.db.add(version)

        await self.db.flush()
        return skill

    async def activate_skill(self, skill_id: str) -> Skill | None:
        """Activate a skill."""
        return await self._update_status(skill_id, "active")

    async def deprecate_skill(self, skill_id: str) -> Skill | None:
        """Deprecate a skill."""
        return await self._update_status(skill_id, "deprecated")

    async def retire_skill(self, skill_id: str) -> Skill | None:
        """Retire a skill."""
        return await self._update_status(skill_id, "retired")

    async def _update_status(self, skill_id: str, status: str) -> Skill | None:
        """Update skill status."""
        skill = await self.get_skill(skill_id)
        if not skill:
            return None

        skill.status = status
        await self.db.flush()
        return skill

    async def record_usage(
        self,
        skill_id: str,
        run_id: str | None = None,
        success: bool = True,
        score_before: float | None = None,
        score_after: float | None = None,
        notes: str | None = None,
    ) -> SkillUsage:
        """Record a skill usage."""
        usage = SkillUsage(
            id=str(uuid4()),
            skill_id=skill_id,
            run_id=run_id,
            success=success,
            score_before=score_before,
            score_after=score_after,
            notes=notes,
        )
        self.db.add(usage)

        # Update skill stats
        skill = await self.get_skill(skill_id)
        if skill:
            skill.times_used += 1
            if success:
                skill.successful_uses += 1
            if score_before is not None and score_after is not None:
                improvement = score_after - score_before
                if skill.average_score_improvement is None:
                    skill.average_score_improvement = improvement
                else:
                    # Running average
                    skill.average_score_improvement = (
                        skill.average_score_improvement * (skill.times_used - 1) + improvement
                    ) / skill.times_used

            # Auto-promote from candidate if used successfully 3+ times
            if skill.status == "candidate" and skill.successful_uses >= 3:
                skill.status = "tested"

        await self.db.flush()
        return usage

    async def evaluate_skill(
        self,
        skill_id: str,
        rating: float,
        feedback: str | None = None,
        evaluator: str = "system",
    ) -> SkillEvaluation:
        """Evaluate a skill."""
        evaluation = SkillEvaluation(
            id=str(uuid4()),
            skill_id=skill_id,
            evaluator=evaluator,
            rating=rating,
            feedback=feedback,
        )
        self.db.add(evaluation)
        await self.db.flush()
        return evaluation

    async def list_skills(
        self,
        project_id: str | None = None,
        skill_type: str | None = None,
        status: str | None = None,
        min_usage: int | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[Skill]:
        """List skills with filters."""
        query = select(Skill)

        if project_id:
            query = query.where(Skill.project_id == project_id)
        if skill_type:
            query = query.where(Skill.skill_type == skill_type)
        if status:
            query = query.where(Skill.status == status)
        if min_usage is not None:
            query = query.where(Skill.times_used >= min_usage)

        offset = (page - 1) * per_page
        query = query.order_by(Skill.times_used.desc()).offset(offset).limit(per_page)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_skills(
        self,
        search_text: str,
        project_id: str | None = None,
    ) -> list[Skill]:
        """Search skills by name, purpose, or procedure."""
        search_pattern = f"%{search_text}%"

        query = select(Skill).where(
            (Skill.name.ilike(search_pattern)) |
            (Skill.purpose.ilike(search_pattern)),
        )

        if project_id:
            query = query.where(Skill.project_id == project_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_relevant_skills(
        self,
        context: str,
        skill_type: str | None = None,
        limit: int = 5,
    ) -> list[Skill]:
        """Get skills relevant to a context."""
        # Simple relevance based on keyword matching
        # In production, would use semantic search
        words = context.lower().split()

        query = select(Skill).where(Skill.status.in_(["active", "tested"]))

        if skill_type:
            query = query.where(Skill.skill_type == skill_type)

        result = await self.db.execute(query.limit(50))
        skills = list(result.scalars().all())

        # Score by keyword overlap
        scored = []
        for skill in skills:
            skill_text = f"{skill.name} {skill.purpose} ".lower()
            skill_text += " ".join(skill.procedure).lower() if skill.procedure else ""
            score = sum(1 for word in words if word in skill_text)
            if score > 0:
                scored.append((score, skill))

        # Sort by score and return top N
        scored.sort(key=lambda x: x[0], reverse=True)
        return [skill for _, skill in scored[:limit]]

    async def get_skill_usage_history(
        self,
        skill_id: str,
    ) -> list[SkillUsage]:
        """Get usage history for a skill."""
        result = await self.db.execute(
            select(SkillUsage)
            .where(SkillUsage.skill_id == skill_id)
            .order_by(SkillUsage.used_at.desc()),
        )
        return list(result.scalars().all())

    async def get_skill_evaluations(
        self,
        skill_id: str,
    ) -> list[SkillEvaluation]:
        """Get evaluations for a skill."""
        result = await self.db.execute(
            select(SkillEvaluation)
            .where(SkillEvaluation.skill_id == skill_id)
            .order_by(SkillEvaluation.created_at.desc()),
        )
        return list(result.scalars().all())

    async def get_skill_statistics(
        self,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Get skill statistics."""
        query = select(Skill)
        if project_id:
            query = query.where(Skill.project_id == project_id)

        result = await self.db.execute(query)
        skills = list(result.scalars().all())

        if not skills:
            return {
                "total_skills": 0,
                "by_status": {},
                "by_type": {},
                "avg_usage": 0,
                "avg_success_rate": 0,
            }

        # By status
        by_status = {}
        for skill in skills:
            by_status[skill.status] = by_status.get(skill.status, 0) + 1

        # By type
        by_type = {}
        for skill in skills:
            by_type[skill.skill_type] = by_type.get(skill.skill_type, 0) + 1

        # Usage stats
        total_usage = sum(s.times_used for s in skills)
        avg_usage = total_usage / len(skills) if skills else 0

        # Success rate
        skills_with_usage = [s for s in skills if s.times_used > 0]
        if skills_with_usage:
            avg_success_rate = sum(
                s.successful_uses / s.times_used for s in skills_with_usage
            ) / len(skills_with_usage)
        else:
            avg_success_rate = 0

        return {
            "total_skills": len(skills),
            "by_status": by_status,
            "by_type": by_type,
            "avg_usage": round(avg_usage, 1),
            "avg_success_rate": round(avg_success_rate * 100, 1),
        }

    async def get_skill_versions(
        self,
        skill_id: str,
    ) -> list[SkillVersion]:
        """Get version history for a skill."""
        result = await self.db.execute(
            select(SkillVersion)
            .where(SkillVersion.skill_id == skill_id)
            .order_by(SkillVersion.created_at),
        )
        return list(result.scalars().all())
