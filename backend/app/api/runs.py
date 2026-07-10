"""Research run API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.dependencies.auth import get_current_user, require_project_role
from app.models.collaboration import User
from app.schemas.audit import AuditLogResponse
from app.schemas.research_run import (
    ResearchRunCreate,
    ResearchRunEventResponse,
    ResearchRunResponse,
    ResearchRunUpdate,
    ToolCallResponse,
)
from app.schemas.research_state import ResearchState
from app.services.audit_service import AuditService
from app.services.research_run_service import ResearchRunService
from app.services.snapshot_service import SnapshotService

router = APIRouter()


@router.get("", response_model=list[ResearchRunResponse])
async def list_runs(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Annotated[str, Query()],
    state: Annotated[str | None, Query()] = None,
    run_type: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
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
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    project_id: Annotated[str, Query()],
    run_in: ResearchRunCreate = ...,
):
    """Create a new research run."""
    await require_project_role(db, project_id, user.id, "editor")
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
    db: Annotated[AsyncSession, Depends(get_db)],
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
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Start a research run."""
    service = ResearchRunService(db)
    existing = await service.get_run(run_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Run not found")
    await require_project_role(db, existing.project_id, user.id, "editor")
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
    db: Annotated[AsyncSession, Depends(get_db)],
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
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Resume a research run. If waiting for approval, continues the workflow."""
    import asyncio

    service = ResearchRunService(db)
    run = await service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.state == "waiting_for_approval":
        from .approvals import _resume_run_after_approval

        await service.update_run(run_id, ResearchRunUpdate(state="running"))
        await db.commit()
        asyncio.create_task(_resume_run_after_approval(run_id))

        audit = AuditService(db)
        await audit.log_run_event(
            run_id=run_id,
            event_type="run_resumed",
            actor="user",
            details={"reason": "approval_resume"},
        )
        run = await service.get_run(run_id)
        return run

    run = await service.resume_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

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
    db: Annotated[AsyncSession, Depends(get_db)],
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
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Cancel a research run."""
    service = ResearchRunService(db)
    existing = await service.get_run(run_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Run not found")
    await require_project_role(db, existing.project_id, user.id, "editor")
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
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get events for a research run."""
    service = ResearchRunService(db)
    events = await service.get_run_events(run_id)
    return events


@router.get("/{run_id}/tools", response_model=list[ToolCallResponse])
async def get_tool_calls(
    run_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get tool calls for a research run."""
    service = ResearchRunService(db)
    tool_calls = await service.get_tool_calls(run_id)
    return tool_calls


@router.get("/{run_id}/status")
async def get_run_status(
    run_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
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
            if event.event_type == "step_completed" and event.details:
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
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get runs for a specific idea."""
    from sqlalchemy import select

    from app.models.research_run import ResearchRun
    result = await db.execute(
        select(ResearchRun).where(ResearchRun.idea_id == idea_id).order_by(ResearchRun.created_at.desc()),
    )
    return list(result.scalars().all())


@router.delete("/{run_id}", status_code=204)
async def delete_run(
    run_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Delete a research run and its associated events and tool calls."""
    from sqlalchemy import delete as sql_delete

    from app.models.research_run import ResearchRun, ResearchRunEvent, ToolCall

    # Check run exists
    service = ResearchRunService(db)
    run = await service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    await require_project_role(db, run.project_id, user.id, "editor")

    # Delete associated tool calls
    await db.execute(
        sql_delete(ToolCall).where(ToolCall.run_id == run_id),
    )
    # Delete associated events
    await db.execute(
        sql_delete(ResearchRunEvent).where(ResearchRunEvent.run_id == run_id),
    )
    # Delete the run itself
    await db.execute(
        sql_delete(ResearchRun).where(ResearchRun.id == run_id),
    )

    # Log the deletion
    audit = AuditService(db)
    await audit.log_event(
        event_type="run_deleted",
        project_id=run.project_id,
        run_id=run_id,
        actor="user",
        action=f"Deleted research run {run_id}",
    )
    await db.commit()


@router.get("/{run_id}/notebook")
async def export_run_notebook(
    run_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Export sandbox experiment as a Jupyter notebook (.ipynb JSON)."""
    from fastapi.responses import JSONResponse

    from app.services.manuscript_context_service import ManuscriptContextService
    from app.services.notebook_export_service import build_notebook

    service = ResearchRunService(db)
    run = await service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    context = ManuscriptContextService(db)
    experiment = await context.get_experiment_for_run(run_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="No experiment results for this run")

    notebook = build_notebook(
        title=f"Experiment — {run_id[:8]}",
        script=experiment.get("script") or "",
        stdout=experiment.get("stdout") or "",
        stderr=experiment.get("stderr") or "",
        artifacts=experiment.get("artifacts"),
    )
    return JSONResponse(
        content=notebook,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="experiment-{run_id[:8]}.ipynb"',
        },
    )


@router.get("/{run_id}/experiment")
async def get_run_experiment(
    run_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get sandbox experiment results persisted for a research run."""
    from app.services.manuscript_context_service import ManuscriptContextService

    service = ResearchRunService(db)
    run = await service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    context = ManuscriptContextService(db)
    experiment = await context.get_experiment_for_run(run_id)
    if not experiment:
        return {
            "run_id": run_id,
            "available": False,
            "message": "No experiment results persisted for this run yet.",
        }

    return {
        "run_id": run_id,
        "available": True,
        **experiment,
    }


@router.get("/{run_id}/snapshot", response_model=ResearchState)
async def get_run_snapshot(
    run_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
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
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Get audit logs for a specific run."""
    audit = AuditService(db)
    logs = await audit.get_run_audit_logs(run_id, limit=limit, offset=offset)
    return logs
