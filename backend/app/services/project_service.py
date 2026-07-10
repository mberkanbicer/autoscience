"""Project service layer."""

from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idea import Idea
from app.models.paper import ClusterConflict, Paper
from app.models.project import Project
from app.models.research_question import Hypothesis, ResearchQuestion
from app.models.research_run import ResearchRun
from app.models.skill import Skill
from app.schemas.project import ProjectCreate, ProjectStats, ProjectUpdate


class ProjectService:
    """Service for project operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_projects(
        self,
        page: int = 1,
        per_page: int = 20,
    ) -> list[Project]:
        """List all projects with pagination."""
        offset = (page - 1) * per_page
        result = await self.db.execute(select(Project).offset(offset).limit(per_page))
        return list(result.scalars().all())

    async def create_project(self, data: ProjectCreate) -> Project:
        """Create a new project."""
        project = Project(
            id=str(uuid4()),
            name=data.name,
            domain=data.domain,
            description=data.description,
            subject_scope=data.subject_scope,
            out_of_scope=data.out_of_scope,
            default_flexibility=data.default_flexibility,
            idle_research_enabled=data.idle_research_enabled,
            idle_trigger_minutes=data.idle_trigger_minutes,
            max_idle_cycles_per_day=data.max_idle_cycles_per_day,
            max_sources_per_cycle=data.max_sources_per_cycle,
            approval_required_for_external_actions=data.approval_required_for_external_actions,
        )
        self.db.add(project)
        await self.db.flush()
        return project

    async def get_project(self, project_id: str) -> Project | None:
        """Get a project by ID."""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def update_project(self, project_id: str, data: ProjectUpdate) -> Project | None:
        """Update a project."""
        project = await self.get_project(project_id)
        if not project:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        await self.db.flush()
        return project

    async def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        project = await self.get_project(project_id)
        if not project:
            return False

        await self.db.delete(project)
        return True

    async def get_project_stats(self, project_id: str) -> ProjectStats | None:
        """Get project statistics."""
        project = await self.get_project(project_id)
        if not project:
            return None

        # Count ideas
        idea_counts = await self.db.execute(
            select(
                func.count(Idea.id).label("total"),
                func.count(Idea.id).filter(Idea.status == "active").label("active"),
                func.count(Idea.id).filter(Idea.status == "rejected").label("rejected"),
            ).where(Idea.project_id == project_id),
        )
        idea_row = idea_counts.one()

        # Count runs
        run_counts = await self.db.execute(
            select(
                func.count(ResearchRun.id).label("total"),
                func.count(ResearchRun.id).filter(ResearchRun.state == "running").label("active"),
            ).where(ResearchRun.project_id == project_id),
        )
        run_row = run_counts.one()

        # Count papers
        paper_count = await self.db.execute(
            select(func.count(Paper.id)).where(Paper.project_id == project_id),
        )

        # Count skills
        skill_count = await self.db.execute(
            select(func.count(Skill.id)).where(Skill.project_id == project_id),
        )

        # Count conflicts
        conflict_count = await self.db.execute(
            select(func.count(ClusterConflict.id)).where(ClusterConflict.project_id == project_id),
        )

        # Count questions
        question_count = await self.db.execute(
            select(func.count(ResearchQuestion.id)).where(ResearchQuestion.project_id == project_id),
        )

        # Count hypotheses
        hypothesis_count = await self.db.execute(
            select(func.count(Hypothesis.id)).where(Hypothesis.project_id == project_id),
        )

        return ProjectStats(
            total_ideas=idea_row.total,
            active_ideas=idea_row.active,
            rejected_ideas=idea_row.rejected,
            total_runs=run_row.total,
            active_runs=run_row.active,
            total_papers=paper_count.scalar() or 0,
            total_skills=skill_count.scalar() or 0,
            total_conflicts=conflict_count.scalar() or 0,
            total_questions=question_count.scalar() or 0,
            total_hypotheses=hypothesis_count.scalar() or 0,
        )
