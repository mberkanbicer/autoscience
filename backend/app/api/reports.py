"""Report and audit API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.dependencies.auth import get_current_user, require_project_role
from app.models.collaboration import User
from app.models.report import ResearchReport as ReportModel
from app.schemas.report import ResearchReportResponse
from app.services.report_service import ReportService

router = APIRouter()


@router.get("", response_model=list[ResearchReportResponse])
async def list_reports(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    project_id: Annotated[str, Query()],
    report_type: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List reports for a project."""
    await require_project_role(db, project_id, user.id, "viewer")
    service = ReportService(db)
    reports = await service.list_reports(project_id, report_type, page, per_page)
    return reports


@router.get("/{report_id}", response_model=ResearchReportResponse)
async def get_report(
    report_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get a report."""
    report = await db.get(ReportModel, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    await require_project_role(db, report.project_id, user.id, "viewer")

    service = ReportService(db)
    return await service.get_report(report_id)


@router.delete("/{report_id}", status_code=204)
async def delete_report(
    report_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Delete a report."""
    from app.services.audit_service import AuditService

    report = await db.get(ReportModel, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    await require_project_role(db, report.project_id, user.id, "editor")

    service = ReportService(db)
    await service.delete_report(report_id)

    audit = AuditService(db)
    await audit.log_event(
        event_type="report_deleted",
        project_id=report.project_id,
        actor=user.display_name,
        action=f"Deleted report {report_id}",
    )
    await db.commit()


@router.get("/{report_id}/export")
async def export_report(
    report_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    format: Annotated[str, Query(pattern="^(markdown|html|json)$")] = "markdown",
):
    """Export a report in the specified format."""
    from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

    report = await db.get(ReportModel, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    await require_project_role(db, report.project_id, user.id, "viewer")

    if format == "markdown":
        content = report.content_markdown or report.content_html or ""
        return PlainTextResponse(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=report-{report.id[:8]}.md"},
        )
    if format == "html":
        content = report.content_html or report.content_markdown or ""
        if not report.content_html:
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
    data = ResearchReportResponse.model_validate(report).model_dump()
    return JSONResponse(
        content=data,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=report-{report.id[:8]}.json"},
    )
