"""Research run API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..services.research_run_service import ResearchRunService
from ..services.audit_service import AuditService
from ..services.snapshot_service import SnapshotService
from ..schemas.research_run import (
    ResearchRunCreate,
    ResearchRunResponse,
    ResearchRunEventResponse,
    ToolCallResponse,
)
from ..schemas.research_state import ResearchState
from ..schemas.audit import AuditLogResponse

router = APIRouter()


@router.get("", response_model=list[ResearchRunResponse])
async def list_runs(
    project_id: str = Query(...),
    state: str | None = Query(None),
    run_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List research runs for a project."""
    service = ResearchRunService(db)
    runs = await service.list_runs(
        project_id=project_id,
        state=state,
        run_type=run_type,
        page=page,
        per_page=per_page,
    )
    return runs


@router.post("", response_model=ResearchRunResponse, status_code=201)
async def create_run(
    project_id: str = Query(...),
    run_in: ResearchRunCreate = ...,
    db: AsyncSession = Depends(get_db),
):
    """Create a new research run."""
    service = ResearchRunService(db)
    run = await service.create_run(project_id=project_id, data=run_in)

    # Log the creation
    audit = AuditService(db)
    await audit.log_event(
        event_type="run_created",
        project_id=project_id,
        run_id=run.id,
        actor="user",
        action=f"Created {run.run_type} research run",
    )

    return run


@router.get("/{run_id}", response_model=ResearchRunResponse)
async def get_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a research run."""
    service = ResearchRunService(db)
    run = await service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/{run_id}/start", response_model=ResearchRunResponse)
async def start_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Start a research run."""
    service = ResearchRunService(db)
    run = await service.start_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Log the start
    audit = AuditService(db)
    await audit.log_run_event(
        run_id=run_id,
        event_type="run_started",
        actor="system",
    )

    return run


@router.post("/{run_id}/pause", response_model=ResearchRunResponse)
async def pause_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Pause a research run."""
    service = ResearchRunService(db)
    run = await service.pause_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Log the pause
    audit = AuditService(db)
    await audit.log_run_event(
        run_id=run_id,
        event_type="run_paused",
        actor="system",
    )

    return run


@router.post("/{run_id}/resume", response_model=ResearchRunResponse)
async def resume_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Resume a research run."""
    service = ResearchRunService(db)
    run = await service.resume_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Log the resume
    audit = AuditService(db)
    await audit.log_run_event(
        run_id=run_id,
        event_type="run_resumed",
        actor="system",
    )

    return run


@router.post("/{run_id}/complete", response_model=ResearchRunResponse)
async def complete_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Complete a research run."""
    service = ResearchRunService(db)
    run = await service.complete_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Log the completion
    audit = AuditService(db)
    await audit.log_run_event(
        run_id=run_id,
        event_type="run_completed",
        actor="system",
    )

    return run


@router.post("/{run_id}/cancel", response_model=ResearchRunResponse)
async def cancel_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a research run."""
    service = ResearchRunService(db)
    run = await service.cancel_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Log the cancellation
    audit = AuditService(db)
    await audit.log_run_event(
        run_id=run_id,
        event_type="run_cancelled",
        actor="system",
    )

    return run


@router.get("/{run_id}/events", response_model=list[ResearchRunEventResponse])
async def get_run_events(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get events for a research run."""
    service = ResearchRunService(db)
    events = await service.get_run_events(run_id)
    return events


@router.get("/{run_id}/tools", response_model=list[ToolCallResponse])
async def get_tool_calls(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get tool calls for a research run."""
    service = ResearchRunService(db)
    tool_calls = await service.get_tool_calls(run_id)
    return tool_calls


@router.get("/{run_id}/status")
async def get_run_status(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get live status of a research run with current phase, recent events, and tool calls."""
    service = ResearchRunService(db)
    run = await service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    events = await service.get_run_events(run_id)
    tool_calls = await service.get_tool_calls(run_id)

    # Determine current phase from latest event
    current_phase = "unknown"
    if events:
        for event in reversed(events):
            if event.event_type == "step_started" and event.details:
                current_phase = event.details.get("step", "unknown")
                break
            elif event.event_type == "step_completed" and event.details:
                current_phase = event.details.get("step", "unknown") + " (done)"
                break

    return {
        "run_id": run.id,
        "state": run.state,
        "current_phase": current_phase,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "event_count": len(events),
        "tool_call_count": len(tool_calls),
        "recent_events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "actor": e.actor,
                "details": e.details,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events[-20:]  # Last 20 events
        ],
        "recent_tool_calls": [
            {
                "id": tc.id,
                "tool_name": tc.tool_name,
                "agent_role": tc.agent_role,
                "success": tc.success,
                "duration_ms": tc.duration_ms,
                "error_message": tc.error_message,
                "created_at": tc.created_at.isoformat() if tc.created_at else None,
            }
            for tc in tool_calls[-20:]  # Last 20 tool calls
        ],
    }


@router.get("/by-idea/{idea_id}")
async def get_runs_by_idea(
    idea_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get runs for a specific idea."""
    from sqlalchemy import select
    from ..models.research_run import ResearchRun
    result = await db.execute(
        select(ResearchRun).where(ResearchRun.idea_id == idea_id).order_by(ResearchRun.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{run_id}/snapshot", response_model=ResearchState)
async def get_run_snapshot(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a complete snapshot of the run's current state."""
    snapshot_service = SnapshotService(db)
    state = await snapshot_service.create_snapshot(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="Run not found")
    return state


@router.get("/{run_id}/audit", response_model=list[AuditLogResponse])
async def get_run_audit_logs(
    run_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get audit logs for a specific run."""
    audit = AuditService(db)
    logs = await audit.get_run_audit_logs(run_id, limit=limit, offset=offset)
    return logs
