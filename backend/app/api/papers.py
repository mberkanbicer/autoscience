"""Paper API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..services.paper_service import PaperService
from ..schemas.paper import (
    PaperCreate,
    PaperUpdate,
    PaperResponse,
    PaperAnalysisResponse,
    PaperClusterResponse,
    ClusterConflictResponse,
)

router = APIRouter()


@router.get("", response_model=list[PaperResponse])
async def list_papers(
    project_id: str = Query(...),
    paper_type: str | None = Query(None),
    year_from: int | None = Query(None),
    year_to: int | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List papers for a project."""
    service = PaperService(db)
    papers = await service.list_papers(
        project_id=project_id,
        paper_type=paper_type,
        year_from=year_from,
        year_to=year_to,
        page=page,
        per_page=per_page,
    )
    return papers


@router.post("", response_model=PaperResponse, status_code=201)
async def create_paper(
    project_id: str = Query(...),
    paper_in: PaperCreate = ...,
    db: AsyncSession = Depends(get_db),
):
    """Create a new paper."""
    service = PaperService(db)
    paper = await service.create_paper(project_id=project_id, data=paper_in)
    return paper


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a paper."""
    service = PaperService(db)
    paper = await service.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router.put("/{paper_id}", response_model=PaperResponse)
async def update_paper(
    paper_id: str,
    paper_in: PaperUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a paper."""
    service = PaperService(db)
    paper = await service.update_paper(paper_id, data=paper_in)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router.delete("/{paper_id}", status_code=204)
async def delete_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a paper."""
    service = PaperService(db)
    deleted = await service.delete_paper(paper_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Paper not found")


@router.get("/{paper_id}/analysis", response_model=PaperAnalysisResponse | None)
async def get_paper_analysis(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get analysis for a paper."""
    service = PaperService(db)
    analysis = await service.get_paper_analysis(paper_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.post("/{paper_id}/analysis", response_model=PaperAnalysisResponse, status_code=201)
async def create_paper_analysis(
    paper_id: str,
    analysis_data: dict,
    db: AsyncSession = Depends(get_db),
):
    """Create or update paper analysis."""
    service = PaperService(db)
    paper = await service.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    analysis = await service.create_paper_analysis(paper_id, analysis_data)
    return analysis


@router.get("/clusters", response_model=list[PaperClusterResponse])
async def list_clusters(
    project_id: str = Query(...),
    cluster_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List paper clusters for a project."""
    service = PaperService(db)
    clusters = await service.list_clusters(project_id, cluster_type)
    return clusters


@router.get("/clusters/{cluster_id}", response_model=PaperClusterResponse)
async def get_cluster(
    cluster_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a cluster."""
    service = PaperService(db)
    cluster = await service.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster


@router.get("/conflicts", response_model=list[ClusterConflictResponse])
async def list_conflicts(
    project_id: str = Query(...),
    conflict_type: str | None = Query(None),
    cluster_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List conflicts for a project."""
    service = PaperService(db)
    conflicts = await service.list_conflicts(project_id, conflict_type, cluster_id)
    return conflicts


@router.get("/conflicts/{conflict_id}", response_model=ClusterConflictResponse)
async def get_conflict(
    conflict_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a conflict."""
    service = PaperService(db)
    conflict = await service.get_conflict(conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    return conflict
