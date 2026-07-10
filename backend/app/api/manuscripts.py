"""Manuscript API endpoints."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.research import get_llm_router
from app.dependencies import get_db
from app.dependencies.auth import get_current_user, require_project_role
from app.models.collaboration import User
from app.models.report import Manuscript as ManuscriptModel
from app.schemas.base import BaseSchema
from app.schemas.manuscript import ManuscriptCreate, ManuscriptResponse, ManuscriptUpdate
from app.services.manuscript_service import ManuscriptService
from app.services.revision_workflow_service import RevisionWorkflowService

router = APIRouter()


class SpawnRevisionRunRequest(BaseSchema):
    """Request schema for spawning a revision run from a manuscript."""
    weaknesses: list[str] = []
    questions: list[str] = []
    summary: str | None = None
    auto_generate_manuscript: bool = True

    model_config = {"extra": "ignore"}


@router.post("/generate", response_model=ManuscriptResponse)
async def generate_manuscript(
    run_id: Annotated[str, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Generate a manuscript from a research run."""
    from app.models.research_run import ResearchRun

    run_result = await db.execute(select(ResearchRun).where(ResearchRun.id == run_id))
    run = run_result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found")
    await require_project_role(db, run.project_id, user.id, "editor")

    service = ManuscriptService(db, get_llm_router())
    try:
        manuscript = await service.generate_for_run(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    await db.commit()
    await db.refresh(manuscript)
    return manuscript


@router.post("", response_model=ManuscriptResponse)
async def create_manuscript(
    data: ManuscriptCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Create a new manuscript."""
    from uuid import uuid4

    await require_project_role(db, data.project_id, user.id, "editor")
    manuscript = ManuscriptModel(
        id=str(uuid4()),
        project_id=data.project_id,
        run_id=data.run_id,
        title=data.title,
        status="draft",
        version=1,
    )
    db.add(manuscript)
    await db.commit()
    await db.refresh(manuscript)
    return manuscript


@router.get("", response_model=list[ManuscriptResponse])
async def list_manuscripts(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Annotated[str, Query()],
    run_id: Annotated[str | None, Query()] = None,
):
    """List manuscripts for a project."""
    query = select(ManuscriptModel).where(ManuscriptModel.project_id == project_id)
    if run_id:
        query = query.where(ManuscriptModel.run_id == run_id)
    query = query.order_by(ManuscriptModel.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/templates/list")
async def list_journal_templates():
    """List available journal LaTeX templates."""
    from app.engine.journal_templates import list_templates
    return list_templates()


@router.post("/{manuscript_id}/apply-template", response_model=ManuscriptResponse)
async def apply_journal_template(
    manuscript_id: str,
    template_id: Annotated[str, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Apply a journal template preamble to manuscript LaTeX."""
    from app.engine.journal_templates import apply_template

    result = await db.execute(
        select(ManuscriptModel).where(ManuscriptModel.id == manuscript_id),
    )
    manuscript = result.scalar_one_or_none()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")
    await require_project_role(db, manuscript.project_id, user.id, "editor")

    manuscript.content_latex = apply_template(template_id, manuscript.content_latex or "")
    manuscript.version += 1
    await db.commit()
    await db.refresh(manuscript)
    return manuscript


@router.get("/{manuscript_id}", response_model=ManuscriptResponse)
async def get_manuscript(
    manuscript_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a manuscript by ID."""
    result = await db.execute(
        select(ManuscriptModel).where(ManuscriptModel.id == manuscript_id),
    )
    manuscript = result.scalar_one_or_none()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")
    return manuscript


@router.patch("/{manuscript_id}", response_model=ManuscriptResponse)
async def update_manuscript(
    manuscript_id: str,
    data: ManuscriptUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Update a manuscript."""
    result = await db.execute(
        select(ManuscriptModel).where(ManuscriptModel.id == manuscript_id),
    )
    manuscript = result.scalar_one_or_none()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")
    await require_project_role(db, manuscript.project_id, user.id, "editor")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(manuscript, field, value)

    if "content_latex" in update_data:
        manuscript.version += 1

    await db.commit()
    await db.refresh(manuscript)
    return manuscript


@router.post("/{manuscript_id}/finalize", response_model=ManuscriptResponse)
async def finalize_manuscript(
    manuscript_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Finalize a manuscript and lock its state."""
    result = await db.execute(
        select(ManuscriptModel).where(ManuscriptModel.id == manuscript_id),
    )
    manuscript = result.scalar_one_or_none()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")
    await require_project_role(db, manuscript.project_id, user.id, "editor")

    manuscript.status = "finalized"
    await db.commit()
    await db.refresh(manuscript)
    return manuscript


@router.post("/{manuscript_id}/compile", response_model=ManuscriptResponse)
async def compile_manuscript(
    manuscript_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Compile manuscript to PDF via server-side pdflatex when available."""
    from app.services.latex_compiler import compile_latex_to_pdf

    result = await db.execute(
        select(ManuscriptModel).where(ManuscriptModel.id == manuscript_id),
    )
    manuscript = result.scalar_one_or_none()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")
    await require_project_role(db, manuscript.project_id, user.id, "editor")

    latex = ManuscriptService.prepare_latex(manuscript)
    pdf_bytes, error = await compile_latex_to_pdf(latex, manuscript.bibtex)
    if pdf_bytes:
        pdf_dir = Path("/tmp/manuscripts")
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_dir / f"{manuscript_id}.pdf"
        pdf_path.write_bytes(pdf_bytes)
        manuscript.compiled_url = (
            f"/api/v1/manuscripts/{manuscript_id}/download?format=pdf"
        )
    else:
        manuscript.compiled_url = (
            f"/api/v1/manuscripts/{manuscript_id}/download?format=tex"
        )
        if error:
            from app.services.audit_service import AuditService

            audit = AuditService(db)
            await audit.log_event(
                event_type="manuscript_compile_fallback",
                project_id=manuscript.project_id,
                actor=user.display_name,
                action=f"PDF compile unavailable: {error}",
                details={"manuscript_id": manuscript_id},
            )

    await db.commit()
    await db.refresh(manuscript)
    return manuscript


@router.post("/{manuscript_id}/spawn-revision-run")
async def spawn_revision_run(
    manuscript_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    body: SpawnRevisionRunRequest = ...,
):
    """Spawn a new research revision run from a manuscript.

    Extracts gaps from the manuscript and optional peer review feedback,
    generates revision research questions, executes a new research run,
    and optionally generates a revised manuscript.
    """
    result = await db.execute(
        select(ManuscriptModel).where(ManuscriptModel.id == manuscript_id),
    )
    manuscript = result.scalar_one_or_none()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")
    await require_project_role(db, manuscript.project_id, user.id, "editor")

    # Build review feedback from the request body
    review_feedback = None
    if body.weaknesses or body.questions:
        review_feedback = {
            "weaknesses": body.weaknesses,
            "questions": body.questions,
            "summary": body.summary or "",
        }

    from app.connectors.manager import ConnectorManager

    connectors = ConnectorManager()
    service = RevisionWorkflowService(
        db=db,
        llm_router=get_llm_router(),
        connector_manager=connectors,
    )

    try:
        result = await service.spawn_revision_run(
            manuscript_id=manuscript_id,
            review_feedback=review_feedback,
            auto_generate_manuscript=body.auto_generate_manuscript,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await db.commit()

    return {
        "parent_manuscript_id": result.parent_manuscript_id,
        "revision_run_id": result.revision_run_id,
        "child_manuscript_id": result.child_manuscript_id,
        "gaps_identified": result.gaps_identified,
        "questions_generated": result.questions_generated,
        "summary": result.summary,
    }


@router.get("/{manuscript_id}/revision-history")
async def get_manuscript_revision_history(
    manuscript_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get the full revision lineage for a manuscript."""
    result = await db.execute(
        select(ManuscriptModel).where(ManuscriptModel.id == manuscript_id),
    )
    manuscript = result.scalar_one_or_none()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")
    await require_project_role(db, manuscript.project_id, user.id, "viewer")

    from app.api.research import get_llm_router

    service = RevisionWorkflowService(
        db=db,
        llm_router=get_llm_router(),
    )
    history = await service.get_revision_history(manuscript_id)
    return history


@router.get("/{manuscript_id}/artifact-links")
async def get_manuscript_artifact_links(
    manuscript_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    section: Annotated[str | None, Query()] = None,
    artifact_type: Annotated[str | None, Query()] = None,
):
    """Get cross-mode artifact links for a manuscript.

    Returns the mapping between experiment artifacts and manuscript sections.
    Supports optional filtering by section (e.g. "results", "methods") and
    artifact_type (e.g. "figure", "table", "claim", "effect_size", "stdout").
    """
    result = await db.execute(
        select(ManuscriptModel).where(ManuscriptModel.id == manuscript_id),
    )
    manuscript = result.scalar_one_or_none()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")
    await require_project_role(db, manuscript.project_id, user.id, "viewer")

    from app.services.artifact_linking_service import ArtifactLinkingService

    linking_service = ArtifactLinkingService(db)
    links = await linking_service.get_links_for_manuscript(
        manuscript_id=manuscript_id,
        section=section,
        artifact_type=artifact_type,
    )
    return links


@router.get("/{manuscript_id}/download")
async def download_manuscript(
    manuscript_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    format: Annotated[str, Query(pattern="^(tex|bib|zip|pdf|docx|md|html)$")] = "tex",
):
    """Download manuscript assets as LaTeX, BibTeX, or a zip bundle."""
    result = await db.execute(
        select(ManuscriptModel).where(ManuscriptModel.id == manuscript_id),
    )
    manuscript = result.scalar_one_or_none()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    safe_title = manuscript.title.replace(" ", "_")

    if format == "md":
        md_content = ManuscriptService.export_markdown(manuscript)
        return Response(
            content=md_content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.md"'},
        )

    if format == "html":
        html_content = ManuscriptService.export_html(manuscript)
        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.html"'},
        )

    if format == "bib":
        return Response(
            content=manuscript.bibtex or "",
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.bib"'},
        )

    if format == "zip":
        bundle = ManuscriptService.export_bundle(manuscript)
        return Response(
            content=bundle,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}_bundle.zip"'},
        )

    if format == "docx":
        docx_bytes, error = await ManuscriptService.export_docx(manuscript)
        if docx_bytes is None:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=501,
                content={
                    "detail": error or "DOCX conversion unavailable. Install pandoc on the server.",
                },
            )
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.docx"'},
        )

    if format == "pdf":
        pdf_path = Path("/tmp/manuscripts") / f"{manuscript_id}.pdf"
        if not pdf_path.exists():
            raise HTTPException(
                status_code=404,
                detail="PDF not compiled yet. POST /compile first.",
            )
        return FileResponse(
            pdf_path,
            filename=f"{safe_title}.pdf",
            media_type="application/pdf",
        )

    latex_path = Path("/tmp/manuscripts") / f"{manuscript_id}.tex"
    latex_path.parent.mkdir(parents=True, exist_ok=True)
    latex_path.write_text(ManuscriptService.prepare_latex(manuscript))
    return FileResponse(
        latex_path,
        filename=f"{safe_title}.tex",
        media_type="text/plain",
    )
