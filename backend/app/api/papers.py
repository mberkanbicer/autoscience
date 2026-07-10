"""Paper API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select as sql_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.dependencies.auth import get_current_user, require_project_role
from app.models.collaboration import User
from app.models.paper import Paper as PaperModel
from app.schemas.paper import (
    ClusterConflictResponse,
    PaperAnalysisResponse,
    PaperClusterResponse,
    PaperCreate,
    PaperResponse,
    PaperUpdate,
)
from app.services.paper_service import PaperService

router = APIRouter()


@router.get("", response_model=list[PaperResponse])
async def list_papers(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Annotated[str, Query()],
    paper_type: Annotated[str | None, Query()] = None,
    cluster_id: Annotated[str | None, Query()] = None,
    year_from: Annotated[int | None, Query()] = None,
    year_to: Annotated[int | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List papers for a project."""
    service = PaperService(db)
    papers = await service.list_papers(
        project_id=project_id,
        paper_type=paper_type,
        cluster_id=cluster_id,
        year_from=year_from,
        year_to=year_to,
        page=page,
        per_page=per_page,
    )
    return papers


@router.post("", response_model=PaperResponse, status_code=201)
async def create_paper(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    project_id: Annotated[str, Query()],
    paper_in: PaperCreate = ...,
):
    """Create a new paper."""
    await require_project_role(db, project_id, user.id, "editor")
    service = PaperService(db)
    paper = await service.create_paper(project_id=project_id, data=paper_in)
    return paper


# IMPORTANT: /clusters, /conflicts, and /search must come BEFORE /{paper_id}
# Otherwise FastAPI matches those paths as a paper_id

@router.get("/arxiv/search")
async def search_arxiv(
    q: Annotated[str, Query(min_length=2)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
):
    """Search arXiv preprints for import."""
    from app.connectors.arxiv import ArxivConnector
    from app.connectors.base import SearchQuery

    connector = ArxivConnector()
    result = await connector.search(SearchQuery(text=q, limit=limit))
    return {
        "query": q,
        "papers": [
            {
                "source": p.source,
                "source_id": p.source_id,
                "title": p.title,
                "authors": p.authors,
                "year": p.year,
                "doi": p.doi,
                "abstract": p.abstract,
                "url": p.url,
            }
            for p in result.papers
        ],
    }


@router.post("/resolve-doi", response_model=PaperResponse)
async def resolve_doi(
    doi: Annotated[str, Query()],
    project_id: Annotated[str, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Resolve DOI metadata via Crossref and create or return project paper."""
    from app.connectors.crossref import CrossrefConnector
    from app.engine.deduplication import normalize_doi

    await require_project_role(db, project_id, user.id, "editor")

    normalized = normalize_doi(doi)
    if not normalized:
        raise HTTPException(status_code=400, detail="Invalid DOI")

    connector = CrossrefConnector()
    raw = await connector.get_paper(normalized)
    if not raw:
        raise HTTPException(status_code=404, detail="DOI not found")

    service = PaperService(db)
    existing = await db.execute(
        sql_select(PaperModel).where(
            PaperModel.project_id == project_id,
            PaperModel.doi == normalized,
        ),
    )
    paper = existing.scalar_one_or_none()
    if not paper:
        from app.schemas.paper import PaperCreate

        paper = await service.create_paper(
            project_id,
            PaperCreate(
                title=raw.title,
                authors=raw.authors,
                year=raw.year,
                doi=raw.doi,
                abstract=raw.abstract,
                venue=raw.venue,
                url=raw.url,
                citation_count=raw.citation_count,
                paper_type=raw.paper_type,
                source_connector=raw.source,
                source_id=raw.source_id,
            ),
        )
        await db.commit()
        await db.refresh(paper)

    return PaperResponse.model_validate(paper)


@router.post("/import-arxiv", response_model=PaperResponse)
async def import_arxiv(
    source_id: Annotated[str, Query(description="arXiv ID, e.g. 2301.00001")],
    project_id: Annotated[str, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Fetch arXiv metadata and create or return project paper."""
    from app.connectors.arxiv import ArxivConnector

    await require_project_role(db, project_id, user.id, "editor")

    connector = ArxivConnector()
    raw = await connector.get_paper(source_id.strip())
    if not raw:
        raise HTTPException(status_code=404, detail="arXiv paper not found")

    existing = await db.execute(
        sql_select(PaperModel).where(
            PaperModel.project_id == project_id,
            PaperModel.source_connector == "arxiv",
            PaperModel.source_id == raw.source_id,
        ),
    )
    paper = existing.scalar_one_or_none()
    if not paper:
        service = PaperService(db)
        paper = await service.create_paper(
            project_id,
            PaperCreate(
                title=raw.title,
                authors=raw.authors,
                year=raw.year,
                doi=raw.doi,
                abstract=raw.abstract,
                venue=raw.venue,
                url=raw.url,
                citation_count=raw.citation_count,
                paper_type=raw.paper_type,
                source_connector=raw.source,
                source_id=raw.source_id,
            ),
        )
        await db.commit()
        await db.refresh(paper)

    return PaperResponse.model_validate(paper)


@router.get("/compare")
async def compare_papers(
    ids: Annotated[str, Query(description="Comma-separated paper IDs (2-5)")],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Side-by-side comparison of paper analyses."""
    paper_ids = [pid.strip() for pid in ids.split(",") if pid.strip()]
    service = PaperService(db)
    try:
        return await service.compare_papers(paper_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/citation-graph")
async def citation_graph(
    project_id: Annotated[str, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Citation graph built from in-corpus paper references."""
    service = PaperService(db)
    return await service.build_citation_graph(project_id)


@router.get("/search/semantic")
async def semantic_paper_search(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Annotated[str, Query()],
    q: Annotated[str, Query(min_length=3)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
):
    """Search project papers by semantic similarity."""
    from app.api.research import get_llm_router
    from app.services.embedding_service import EmbeddingService

    service = EmbeddingService(db, get_llm_router())
    try:
        results = await service.search_similar(project_id, q, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"query": q, "results": results}


@router.get("/clusters", response_model=list[PaperClusterResponse])
async def list_clusters(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Annotated[str, Query()],
    cluster_type: Annotated[str | None, Query()] = None,
    run_id: Annotated[str | None, Query()] = None,
):
    """List paper clusters for a project."""
    service = PaperService(db)
    clusters = await service.list_clusters(project_id, cluster_type, run_id)
    return clusters


@router.get("/clusters/{cluster_id}", response_model=PaperClusterResponse)
async def get_cluster(
    cluster_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a cluster."""
    service = PaperService(db)
    cluster = await service.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster


@router.get("/conflicts", response_model=list[ClusterConflictResponse])
async def list_conflicts(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Annotated[str, Query()],
    conflict_type: Annotated[str | None, Query()] = None,
    cluster_id: Annotated[str | None, Query()] = None,
    run_id: Annotated[str | None, Query()] = None,
):
    """List conflicts for a project."""
    service = PaperService(db)
    conflicts = await service.list_conflicts(project_id, conflict_type, cluster_id, run_id)
    return conflicts


@router.get("/conflicts/{conflict_id}", response_model=ClusterConflictResponse)
async def get_conflict(
    conflict_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a conflict."""
    service = PaperService(db)
    conflict = await service.get_conflict(conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    return conflict


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
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
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Update a paper."""
    result = await db.execute(sql_select(PaperModel).where(PaperModel.id == paper_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Paper not found")
    await require_project_role(db, existing.project_id, user.id, "editor")

    service = PaperService(db)
    paper = await service.update_paper(paper_id, data=paper_in)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router.delete("/{paper_id}", status_code=204)
async def delete_paper(
    paper_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Delete a paper."""
    from app.services.audit_service import AuditService

    result = await db.execute(sql_select(PaperModel).where(PaperModel.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    await require_project_role(db, paper.project_id, user.id, "editor")

    service = PaperService(db)
    await service.delete_paper(paper_id)

    # Log the deletion
    audit = AuditService(db)
    await audit.log_event(
        event_type="paper_deleted",
        project_id=paper.project_id,
        actor="user",
        action=f"Deleted paper {paper_id}",
    )
    await db.commit()


@router.get("/{paper_id}/analysis", response_model=PaperAnalysisResponse | None)
async def get_paper_analysis(
    paper_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
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
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create or update paper analysis."""
    service = PaperService(db)
    paper = await service.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    analysis = await service.create_paper_analysis(paper_id, analysis_data)
    return analysis
