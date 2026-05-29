"""Skill API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..services.skill_service import SkillService
from ..schemas.skill import (
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    SkillVersionResponse,
    SkillUsageResponse,
)

router = APIRouter()


@router.get("", response_model=list[SkillResponse])
async def list_skills(
    project_id: str | None = Query(None),
    skill_type: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List skills with optional filters."""
    service = SkillService(db)
    skills = await service.list_skills(
        project_id=project_id,
        skill_type=skill_type,
        status=status,
        page=page,
        per_page=per_page,
    )
    return skills


@router.post("", response_model=SkillResponse, status_code=201)
async def create_skill(
    skill_in: SkillCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new skill."""
    service = SkillService(db)
    skill = await service.create_skill(data=skill_in)
    return skill


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a skill."""
    service = SkillService(db)
    skill = await service.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    skill_in: SkillUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a skill."""
    service = SkillService(db)
    skill = await service.update_skill(skill_id, data=skill_in)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.delete("/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a skill."""
    service = SkillService(db)
    deleted = await service.delete_skill(skill_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Skill not found")


@router.post("/{skill_id}/retire", response_model=SkillResponse)
async def retire_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retire a skill."""
    service = SkillService(db)
    skill = await service.retire_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.get("/{skill_id}/versions", response_model=list[SkillVersionResponse])
async def get_skill_versions(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get skill version history."""
    service = SkillService(db)
    versions = await service.get_skill_versions(skill_id)
    return versions


@router.get("/{skill_id}/usage", response_model=list[SkillUsageResponse])
async def get_skill_usage(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get skill usage history."""
    service = SkillService(db)
    usage = await service.get_skill_usage(skill_id)
    return usage
