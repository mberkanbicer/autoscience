"""Idea API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..services.idea_service import IdeaService
from ..schemas.idea import (
    IdeaCreate,
    IdeaUpdate,
    IdeaResponse,
    IdeaDetailResponse,
    IdeaVersionResponse,
    IdeaDecisionResponse,
)

router = APIRouter()


@router.get("", response_model=list[IdeaResponse])
async def list_ideas(
    project_id: str = Query(...),
    status: str | None = Query(None),
    classification: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List ideas for a project."""
    service = IdeaService(db)
    ideas = await service.list_ideas(
        project_id=project_id,
        status=status,
        classification=classification,
        page=page,
        per_page=per_page,
    )
    return ideas


@router.post("", response_model=IdeaResponse, status_code=201)
async def create_idea(
    project_id: str = Query(...),
    idea_in: IdeaCreate = ...,
    db: AsyncSession = Depends(get_db),
):
    """Create a new idea."""
    service = IdeaService(db)
    idea = await service.create_idea(project_id=project_id, data=idea_in)
    return idea


@router.get("/{idea_id}", response_model=IdeaDetailResponse)
async def get_idea(
    idea_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get idea details."""
    service = IdeaService(db)
    idea = await service.get_idea(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    versions = await service.get_idea_versions(idea_id)
    scores = await service.get_idea_scores(idea_id)
    decisions = await service.get_idea_decisions(idea_id)

    return IdeaDetailResponse(
        id=idea.id,
        created_at=idea.created_at,
        updated_at=idea.updated_at,
        project_id=idea.project_id,
        origin=idea.origin,
        initial_text=idea.initial_text,
        current_text=idea.current_text,
        flexibility=idea.flexibility,
        status=idea.status,
        classification=idea.classification,
        overall_score=idea.overall_score,
        classification_reason=idea.classification_reason,
        scores=scores,
        versions=versions,
        decisions=decisions,
    )


@router.put("/{idea_id}", response_model=IdeaResponse)
async def update_idea(
    idea_id: str,
    idea_in: IdeaUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an idea."""
    service = IdeaService(db)
    idea = await service.update_idea(idea_id, data=idea_in)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    return idea


@router.delete("/{idea_id}", status_code=204)
async def delete_idea(
    idea_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an idea."""
    service = IdeaService(db)
    deleted = await service.delete_idea(idea_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Idea not found")


@router.get("/{idea_id}/versions", response_model=list[IdeaVersionResponse])
async def get_idea_versions(
    idea_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get idea version history."""
    service = IdeaService(db)
    versions = await service.get_idea_versions(idea_id)
    return versions


@router.get("/{idea_id}/decisions", response_model=list[IdeaDecisionResponse])
async def get_idea_decisions(
    idea_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get idea decision history."""
    service = IdeaService(db)
    decisions = await service.get_idea_decisions(idea_id)
    return decisions
