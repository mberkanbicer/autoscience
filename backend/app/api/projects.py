"""Project API endpoints."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..models.project import Project
from ..schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectStats,
)

router = APIRouter()


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[Project]:
    """List all projects."""
    offset = (page - 1) * per_page
    result = await db.execute(select(Project).offset(offset).limit(per_page))
    return result.scalars().all()


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Create a new project."""
    project = Project(
        id=str(uuid4()),
        name=project_in.name,
        domain=project_in.domain,
        description=project_in.description,
        subject_scope=project_in.subject_scope,
        out_of_scope=project_in.out_of_scope,
        default_flexibility=project_in.default_flexibility,
        idle_research_enabled=project_in.idle_research_enabled,
        idle_trigger_minutes=project_in.idle_trigger_minutes,
        max_idle_cycles_per_day=project_in.max_idle_cycles_per_day,
        max_sources_per_cycle=project_in.max_sources_per_cycle,
        approval_required_for_external_actions=project_in.approval_required_for_external_actions,
    )
    db.add(project)
    await db.flush()
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Get a project by ID."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Update a project."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.flush()
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a project."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)


@router.get("/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectStats:
    """Get project statistics."""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Count ideas
    from ..models.idea import Idea

    idea_counts = await db.execute(
        select(
            func.count(Idea.id).label("total"),
            func.count(Idea.id).filter(Idea.status == "active").label("active"),
            func.count(Idea.id).filter(Idea.status == "rejected").label("rejected"),
        ).where(Idea.project_id == project_id)
    )
    idea_row = idea_counts.one()

    # Count runs
    from ..models.research_run import ResearchRun

    run_counts = await db.execute(
        select(
            func.count(ResearchRun.id).label("total"),
            func.count(ResearchRun.id).filter(ResearchRun.state == "running").label("active"),
        ).where(ResearchRun.project_id == project_id)
    )
    run_row = run_counts.one()

    # Count papers
    from ..models.paper import Paper

    paper_count = await db.execute(
        select(func.count(Paper.id)).where(Paper.project_id == project_id)
    )

    # Count skills
    from ..models.skill import Skill

    skill_count = await db.execute(
        select(func.count(Skill.id)).where(Skill.project_id == project_id)
    )

    # Count conflicts
    from ..models.paper import ClusterConflict

    conflict_count = await db.execute(
        select(func.count(ClusterConflict.id)).where(ClusterConflict.project_id == project_id)
    )

    # Count questions
    from ..models.research_question import ResearchQuestion

    question_count = await db.execute(
        select(func.count(ResearchQuestion.id)).where(ResearchQuestion.project_id == project_id)
    )

    # Count hypotheses
    from ..models.research_question import Hypothesis

    hypothesis_count = await db.execute(
        select(func.count(Hypothesis.id)).where(Hypothesis.project_id == project_id)
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
