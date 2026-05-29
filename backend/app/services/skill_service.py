"""Skill service layer."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.skill import Skill, SkillVersion, SkillUsage
from ..schemas.skill import SkillCreate, SkillUpdate


class SkillService:
    """Service for skill operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_skills(
        self,
        project_id: str | None = None,
        skill_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[Skill]:
        """List skills with optional filters."""
        query = select(Skill)

        if project_id:
            query = query.where(Skill.project_id == project_id)
        if skill_type:
            query = query.where(Skill.skill_type == skill_type)
        if status:
            query = query.where(Skill.status == status)

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_skill(
        self,
        data: SkillCreate,
    ) -> Skill:
        """Create a new skill."""
        skill = Skill(
            id=str(uuid4()),
            project_id=data.project_id,
            name=data.name,
            skill_type=data.skill_type,
            purpose=data.purpose,
            trigger_conditions=data.trigger_conditions,
            inputs=data.inputs,
            procedure=data.procedure,
            outputs=data.outputs,
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
            procedure=data.procedure,
        )
        self.db.add(version)

        await self.db.flush()
        return skill

    async def get_skill(self, skill_id: str) -> Skill | None:
        """Get a skill by ID."""
        result = await self.db.execute(select(Skill).where(Skill.id == skill_id))
        return result.scalar_one_or_none()

    async def update_skill(self, skill_id: str, data: SkillUpdate) -> Skill | None:
        """Update a skill."""
        skill = await self.get_skill(skill_id)
        if not skill:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # If procedure changed, create a new version
        if "procedure" in update_data and update_data["procedure"] != skill.procedure:
            # Increment version
            major, minor = skill.version.split(".")
            new_version_str = f"{major}.{int(minor) + 1}"

            version = SkillVersion(
                id=str(uuid4()),
                skill_id=skill_id,
                version=new_version_str,
                changes="Updated via API",
                procedure=update_data["procedure"],
            )
            self.db.add(version)
            skill.version = new_version_str

        for field, value in update_data.items():
            setattr(skill, field, value)

        await self.db.flush()
        return skill

    async def delete_skill(self, skill_id: str) -> bool:
        """Delete a skill."""
        skill = await self.get_skill(skill_id)
        if not skill:
            return False

        await self.db.delete(skill)
        return True

    async def retire_skill(self, skill_id: str) -> Skill | None:
        """Retire a skill."""
        return await self.update_skill(skill_id, SkillUpdate(status="retired"))

    async def get_skill_versions(self, skill_id: str) -> list[SkillVersion]:
        """Get version history for a skill."""
        result = await self.db.execute(
            select(SkillVersion)
            .where(SkillVersion.skill_id == skill_id)
            .order_by(SkillVersion.created_at)
        )
        return list(result.scalars().all())

    async def get_skill_usage(self, skill_id: str) -> list[SkillUsage]:
        """Get usage history for a skill."""
        result = await self.db.execute(
            select(SkillUsage)
            .where(SkillUsage.skill_id == skill_id)
            .order_by(SkillUsage.used_at)
        )
        return list(result.scalars().all())

    async def record_skill_usage(
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

        await self.db.flush()
        return usage
