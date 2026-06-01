"""Report and audit API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..services.report_service import ReportService, KnowledgeService
from ..schemas.report import (
    ResearchReportResponse,
    KnowledgeNoteCreate,
    KnowledgeNoteResponse,
)

router = APIRouter()


# Reports

@router.get("/reports", response_model=list[ResearchReportResponse])
async def list_reports(
    project_id: str = Query(...),
    report_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List reports for a project."""
    service = ReportService(db)
    reports = await service.list_reports(project_id, report_type, page, per_page)
    return reports


@router.get("/reports/{report_id}", response_model=ResearchReportResponse)
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a report."""
    service = ReportService(db)
    report = await service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.delete("/reports/{report_id}", status_code=204)
async def delete_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a report."""
    service = ReportService(db)
    deleted = await service.delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")


@router.get("/reports/{report_id}/export")
async def export_report(
    report_id: str,
    format: str = Query("markdown", regex="^(markdown|html|json)$"),
    db: AsyncSession = Depends(get_db),
):
    """Export a report in the specified format."""
    from fastapi.responses import PlainTextResponse, HTMLResponse, JSONResponse
    from sqlalchemy import select
    from ..models.report import ResearchReport as ReportModel

    result = await db.execute(select(ReportModel).where(ReportModel.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if format == "markdown":
        content = report.content_markdown or report.content_html or ""
        return PlainTextResponse(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=report-{report.id[:8]}.md"},
        )
    elif format == "html":
        content = report.content_html or report.content_markdown or ""
        if not report.content_html:
            # Convert markdown to basic HTML
            import re
            content = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{report.title or 'Report'}</title>
<style>body{{max-width:800px;margin:auto;padding:2em;font-family:system-ui,sans-serif;line-height:1.6}}
pre{{background:#f4f4f4;padding:1em;border-radius:8px;overflow-x:auto}}
code{{background:#f4f4f4;padding:0.2em 0.4em;border-radius:4px;font-size:0.9em}}
img{{max-width:100%}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
</style></head><body><h1>{report.title or 'Research Report'}</h1><div>{content.replace(chr(10), '<br>')}</div></body></html>"""
        return HTMLResponse(
            content=content,
            headers={"Content-Disposition": f"attachment; filename=report-{report.id[:8]}.html"},
        )
    else:  # json
        from ..schemas.report import ResearchReportResponse
        data = ResearchReportResponse.model_validate(report).model_dump()
        return JSONResponse(
            content=data,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=report-{report.id[:8]}.json"},
        )


# Knowledge Wiki

@router.get("/wiki", response_model=list[KnowledgeNoteResponse])
async def list_wiki_notes(
    project_id: str = Query(...),
    note_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List knowledge notes for a project."""
    service = KnowledgeService(db)
    notes = await service.list_notes(project_id, note_type, page, per_page)
    return notes


@router.post("/wiki", response_model=KnowledgeNoteResponse, status_code=201)
async def create_wiki_note(
    project_id: str = Query(...),
    note_in: KnowledgeNoteCreate = ...,
    db: AsyncSession = Depends(get_db),
):
    """Create a new knowledge note."""
    service = KnowledgeService(db)
    note = await service.create_note(
        project_id=project_id,
        note_type=note_in.note_type,
        title=note_in.title,
        content=note_in.content,
        entity_id=note_in.entity_id,
        linked_notes=note_in.linked_notes,
    )
    return note


@router.get("/wiki/{note_id}", response_model=KnowledgeNoteResponse)
async def get_wiki_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a knowledge note."""
    service = KnowledgeService(db)
    note = await service.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.put("/wiki/{note_id}", response_model=KnowledgeNoteResponse)
async def update_wiki_note(
    note_id: str,
    title: str | None = Query(None),
    content: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Update a knowledge note."""
    service = KnowledgeService(db)
    note = await service.update_note(note_id, title=title, content=content)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/wiki/{note_id}", status_code=204)
async def delete_wiki_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a knowledge note."""
    service = KnowledgeService(db)
    deleted = await service.delete_note(note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")


# Approvals

@router.get("/approvals", response_model=list[dict])
async def list_approvals(
    project_id: str = Query(...),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List approval requests for a project."""
    from sqlalchemy import select
    from ..models.audit import ApprovalRequest

    query = select(ApprovalRequest).where(ApprovalRequest.project_id == project_id)
    if status:
        query = query.where(ApprovalRequest.status == status)
    query = query.order_by(ApprovalRequest.created_at.desc())

    result = await db.execute(query)
    approvals = list(result.scalars().all())
    return approvals


@router.post("/approvals/{approval_id}/approve", response_model=dict)
async def approve_request(
    approval_id: str,
    body: dict = {},
    db: AsyncSession = Depends(get_db),
):
    """Approve a pending request."""
    from sqlalchemy import select
    from ..models.audit import ApprovalRequest

    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    approval.status = "approved"
    await db.flush()
    await db.refresh(approval)
    return {"id": approval.id, "status": approval.status}


@router.post("/approvals/{approval_id}/deny", response_model=dict)
async def deny_request(
    approval_id: str,
    body: dict = {},
    db: AsyncSession = Depends(get_db),
):
    """Deny a pending request."""
    from sqlalchemy import select
    from ..models.audit import ApprovalRequest

    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    approval.status = "denied"
    await db.flush()
    await db.refresh(approval)
    return {"id": approval.id, "status": approval.status}
