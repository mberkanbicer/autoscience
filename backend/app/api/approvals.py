"""Approval API endpoints."""

import asyncio
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.dependencies import get_db
from app.dependencies.auth import get_current_user, require_project_role
from app.models.collaboration import User
from app.schemas.audit import ApprovalDecision, ApprovalRequestResponse
from app.services.research_run_service import ResearchRunService
from app.services.safety_service import SafetyService

logger = structlog.get_logger()

router = APIRouter()


async def _resume_run_after_approval(run_id: str) -> None:
    """Resume a gated research run in the background after approval."""
    from app.config import get_settings
    from app.services.event_stream import EventBroadcaster
    from app.services.orchestrator import ResearchOrchestrator

    from .research import get_connector_manager, get_llm_router

    settings = get_settings()
    llm_router = get_llm_router()
    connector_manager = get_connector_manager()

    event_broadcaster = None
    try:
        import redis.asyncio as aioredis
        redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
        event_broadcaster = EventBroadcaster(redis_client)
    except (ImportError, ConnectionError, OSError):
        logger.debug("redis_unavailable_for_approval")
    except Exception as exc:
        logger.warning("redis_unexpected_for_approval", error=str(exc), exc_info=True)

    try:
        async with async_session_factory() as db:
            orchestrator = ResearchOrchestrator(
                db=db,
                llm_router=llm_router,
                connector_manager=connector_manager,
                event_broadcaster=event_broadcaster,
            )
            await orchestrator.resume_research(run_id)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error("resume_after_approval_failed", run_id=run_id, error=str(e))


@router.get("", response_model=list[ApprovalRequestResponse])
async def list_approvals(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    project_id: Annotated[str, Query()],
    status: Annotated[str | None, Query()] = None,
):
    """List approval requests for a project."""
    await require_project_role(db, project_id, user.id, "viewer")
    safety = SafetyService(db)
    if status == "pending":
        return await safety.get_pending_approvals(project_id=project_id)

    from sqlalchemy import select

    from app.models.audit import ApprovalRequest

    query = select(ApprovalRequest).where(ApprovalRequest.project_id == project_id)
    if status:
        query = query.where(ApprovalRequest.status == status)
    query = query.order_by(ApprovalRequest.created_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/{approval_id}/approve", response_model=dict)
async def approve_request(
    approval_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    decision: ApprovalDecision | None = None,
):
    """Approve a pending request and resume the linked run if applicable."""
    from app.models.audit import ApprovalRequest

    pending = await db.get(ApprovalRequest, approval_id)
    if not pending:
        raise HTTPException(status_code=404, detail="Approval not found")
    await require_project_role(db, pending.project_id, user.id, "editor")

    safety = SafetyService(db)
    approval = await safety.approve_request(
        approval_id,
        approved=True,
        reason=decision.reviewer_notes if decision else None,
    )
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    await db.commit()

    if approval.run_id:
        asyncio.create_task(_resume_run_after_approval(approval.run_id))

    return {"id": approval.id, "status": approval.status, "run_id": approval.run_id}


@router.post("/{approval_id}/deny", response_model=dict)
async def deny_request(
    approval_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    decision: ApprovalDecision | None = None,
):
    """Deny a pending request and mark the linked run as failed."""
    from app.models.audit import ApprovalRequest

    pending = await db.get(ApprovalRequest, approval_id)
    if not pending:
        raise HTTPException(status_code=404, detail="Approval not found")
    await require_project_role(db, pending.project_id, user.id, "editor")

    safety = SafetyService(db)
    approval = await safety.approve_request(
        approval_id,
        approved=False,
        reason=decision.reviewer_notes if decision else "Denied by user",
    )
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    if approval.run_id:
        run_service = ResearchRunService(db)
        await run_service.fail_run(
            approval.run_id,
            error=decision.reviewer_notes if decision else "Approval denied",
        )

    await db.commit()
    return {"id": approval.id, "status": approval.status, "run_id": approval.run_id}
