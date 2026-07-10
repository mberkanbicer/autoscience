"""Skill API endpoints."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select as sql_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings

# CORS headers for SSE
SSE_CORS_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Credentials": "true",
}    # Channel used by the scheduler for broadcasting skill evaluation events
_SYSTEM_EVAL_CHANNEL = "run:__system_skill_eval:events"

import structlog

logger = structlog.get_logger()

from app.dependencies import get_db
from app.dependencies.auth import get_current_user, require_project_role
from app.models.collaboration import User
from app.models.skill import Skill as SkillModel
from app.schemas.base import BaseSchema
from app.schemas.skill import (
    SkillCreate,
    SkillResponse,
    SkillUpdate,
    SkillUsageResponse,
    SkillVersionResponse,
)
from app.services.skill_performance_service import SkillPerformanceService
from app.services.skill_service import SkillService

router = APIRouter()


async def _require_skill_role(
    db: AsyncSession,
    skill_id: str,
    user_id: str,
    min_role: str,
) -> SkillModel:
    result = await db.execute(sql_select(SkillModel).where(SkillModel.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    if skill.project_id:
        await require_project_role(db, skill.project_id, user_id, min_role)
    return skill


@router.get("", response_model=list[SkillResponse])
async def list_skills(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    project_id: Annotated[str | None, Query()] = None,
    skill_type: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List skills with optional filters."""
    if project_id:
        await require_project_role(db, project_id, user.id, "viewer")
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
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Create a new skill."""
    if skill_in.project_id:
        await require_project_role(db, skill_in.project_id, user.id, "editor")
    service = SkillService(db)
    skill = await service.create_skill(data=skill_in)
    return skill


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get a skill."""
    await _require_skill_role(db, skill_id, user.id, "viewer")
    service = SkillService(db)
    skill = await service.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    skill_in: SkillUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Update a skill."""
    await _require_skill_role(db, skill_id, user.id, "editor")
    service = SkillService(db)
    skill = await service.update_skill(skill_id, data=skill_in)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.delete("/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Delete a skill."""
    from app.services.audit_service import AuditService

    skill = await _require_skill_role(db, skill_id, user.id, "editor")

    service = SkillService(db)
    await service.delete_skill(skill_id)

    audit = AuditService(db)
    await audit.log_event(
        event_type="skill_deleted",
        project_id=skill.project_id,
        actor=user.display_name,
        action=f"Deleted skill {skill_id}",
    )
    await db.commit()


@router.post("/{skill_id}/retire", response_model=SkillResponse)
async def retire_skill(
    skill_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Retire a skill."""
    await _require_skill_role(db, skill_id, user.id, "editor")
    service = SkillService(db)
    skill = await service.retire_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.get("/{skill_id}/versions", response_model=list[SkillVersionResponse])
async def get_skill_versions(
    skill_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get skill version history."""
    await _require_skill_role(db, skill_id, user.id, "viewer")
    service = SkillService(db)
    versions = await service.get_skill_versions(skill_id)
    return versions


@router.get("/{skill_id}/usage", response_model=list[SkillUsageResponse])
async def get_skill_usage(
    skill_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get skill usage history."""
    await _require_skill_role(db, skill_id, user.id, "viewer")
    service = SkillService(db)
    usage = await service.get_skill_usage(skill_id)
    return usage


def _broadcast_eval_event(result: dict) -> None:
    """Best-effort broadcast of an evaluation result to the SSE channel.

    This is a synchronous fire-and-forget function — it creates an ephemeral
    Redis connection, publishes the event, and closes immediately. This avoids
    blocking the API response on Redis availability.

    The scheduler's _run_evaluation uses EventBroadcaster for the same purpose.
    """
    import asyncio
    import json
    import time

    try:
        settings = get_settings()
        import redis.asyncio as aioredis

        async def _publish():
            redis_client = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_keepalive=True,
                socket_timeout=3,
            )
            try:
                event_type = "skill_eval_error" if result.get("errors") else "skill_eval_completed"
                # Use a millisecond timestamp so every manual trigger gets a unique
                # run_number — the frontend hook deduplicates by this value.
                manual_run_number = int(time.time() * 1000)
                event = {
                    "type": event_type,
                    "data": {
                        "evaluated_count": result.get("evaluated_count", 0),
                        "deprecated_count": len(result.get("deprecated", [])),
                        "retired_count": len(result.get("retired", [])),
                        "error_count": len(result.get("errors", [])),
                        "dry_run": result.get("dry_run", False),
                        "summary": result.get("summary", ""),
                        "run_number": manual_run_number,
                    },
                }
                await redis_client.publish(_SYSTEM_EVAL_CHANNEL, json.dumps(event, default=str))
            finally:
                await redis_client.close()

        asyncio.create_task(_publish())
    except (ConnectionError, OSError):
        pass  # Redis unavailable — broadcast is best-effort
    except Exception as e:
        logger.debug("eval_broadcast_unexpected", error=str(e), exc_info=True)


class EvaluateSkillsRequest(BaseSchema):
    """Request schema for triggering skill performance evaluation."""
    dry_run: bool = False
    project_id: str | None = None


@router.post("/evaluate")
async def evaluate_skills(
    body: EvaluateSkillsRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Trigger skill performance evaluation.

    Evaluates all skills against performance thresholds (success rate, score impact)
    and auto-deprecates/retires low-performing skills.

    Use `dry_run=true` to preview what would happen without making changes.

    The result is also broadcast via the SSE event channel when Redis is
    available, so other sessions receive a real-time toast notification.
    """
    if body.project_id:
        await require_project_role(db, body.project_id, user.id, "editor")
    service = SkillPerformanceService(db)
    result = await service.evaluate_all_skills(
        project_id=body.project_id,
        dry_run=body.dry_run,
    )

    response_data = {
        "evaluated_count": result.evaluated_count,
        "deprecated": [r.skill_name for r in result.deprecated],
        "retired": [r.skill_name for r in result.retired],
        "errors": result.errors,
        "summary": result.summary,
        "dry_run": body.dry_run,
    }

    # Broadcast to SSE channel when Redis is available
    _broadcast_eval_event(response_data)

    return response_data


@router.get("/performance/history")
async def skill_performance_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    project_id: Annotated[str | None, Query()] = None,
    skill_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    """Get time-series performance history from skill evaluations.

    Returns success rate, avg score improvement, and usage at each
    evaluation point, ordered by timestamp. Suitable for chart rendering.

    Optionally filter by project or individual skill.
    """
    if project_id:
        await require_project_role(db, project_id, user.id, "viewer")
    if skill_id:
        from sqlalchemy import select

        from app.models.skill import Skill as SkillModel
        sk_result = await db.execute(select(SkillModel).where(SkillModel.id == skill_id))
        sk = sk_result.scalar_one_or_none()
        if sk and sk.project_id:
            await require_project_role(db, sk.project_id, user.id, "viewer")
    service = SkillPerformanceService(db)
    return await service.get_performance_history(
        project_id=project_id,
        skill_id=skill_id,
        limit=limit,
    )


@router.get("/performance/scheduler-status")
async def skill_eval_scheduler_status():
    """Get the current skill evaluation scheduler status."""
    from app.services.skill_evaluation_scheduler import get_scheduler_status
    return get_scheduler_status()


class SchedulerConfigUpdate(BaseSchema):
    """Request schema for updating scheduler runtime config."""
    enabled: bool | None = None
    interval_hours: int | None = None
    dry_run: bool | None = None


@router.get("/performance/scheduler-config")
async def skill_eval_scheduler_config():
    """Get the current scheduler runtime configuration."""
    from app.services.skill_evaluation_scheduler import get_scheduler_config
    return get_scheduler_config()


@router.patch("/performance/scheduler-config")
async def skill_eval_update_scheduler_config(
    body: SchedulerConfigUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Update scheduler runtime configuration and restart if needed.

    Changes take effect immediately: the scheduler is stopped and
    restarted with the new settings when enabled.
    """
    from app.database import async_session_factory
    from app.services.skill_evaluation_scheduler import update_scheduler_config

    # Attempt Redis connection for event broadcasting
    redis_client = None
    try:
        import redis.asyncio as aioredis
        settings = get_settings()
        redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_keepalive=True,
            socket_timeout=5,
        )
    except (ImportError, ConnectionError, OSError) as exc:
        logger.debug("redis_unavailable_for_scheduler", error=str(exc))
    except Exception as exc:
        logger.warning("redis_connection_unexpected", error=str(exc))

    new_config = await update_scheduler_config(
        db_factory=async_session_factory,
        enabled=body.enabled,
        interval_hours=body.interval_hours,
        dry_run=body.dry_run,
        redis_client=redis_client,
    )
    return new_config


@router.get("/performance/eval-history")
async def skill_eval_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    """Get past scheduled evaluation events from the audit log.

    Returns audit log entries filtered by event_type="skill_evaluation_scheduled",
    ordered by newest first. Each entry includes details about evaluated count,
    deprecated/retired counts, errors, and dry_run mode.
    """
    from sqlalchemy import select

    from app.models.audit import AuditLog

    query = (
        select(AuditLog)
        .where(AuditLog.event_type == "skill_evaluation_scheduled")
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        {
            "id": log.id,
            "timestamp": log.created_at.isoformat() if log.created_at else None,
            "event_type": log.event_type,
            "action": log.action,
            "details": log.details or {},
        }
        for log in logs
    ]


@router.get("/performance/stats")
async def skill_performance_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    project_id: Annotated[str | None, Query()] = None,
):
    """Get aggregate skill performance statistics."""
    if project_id:
        await require_project_role(db, project_id, user.id, "viewer")
    service = SkillPerformanceService(db)
    return await service.get_performance_stats(project_id=project_id)


async def _eval_event_generator() -> AsyncGenerator[str, None]:
    """Generate SSE frames from the system skill-eval Redis channel."""
    import json

    import redis.asyncio as aioredis

    settings = get_settings()
    redis_client = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_keepalive=True,
        socket_timeout=None,
    )
    pubsub = redis_client.pubsub()
    try:
        await pubsub.subscribe(_SYSTEM_EVAL_CHANNEL)
        # Send initial connected event
        yield f"data: {json.dumps({'type': 'connected', 'data': {}})}\n\n"

        while True:
            try:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=30.0,
                )
            except asyncio.CancelledError:
                break

            if message and message.get("type") == "message":
                data = message.get("data")
                if isinstance(data, bytes):
                    data = data.decode()
                yield f"data: {data}\n\n"
            else:
                # Send keepalive to prevent timeout
                yield ": keepalive\n\n"
    finally:
        try:
            await pubsub.unsubscribe()
            await pubsub.close()
        except (ConnectionError, OSError):
            pass
        except Exception:
            logger.debug("eval_stream_pubsub_cleanup_failed", exc_info=True)
        try:
            await redis_client.close()
        except (ConnectionError, OSError):
            pass
        except Exception:
            logger.debug("eval_stream_redis_cleanup_failed", exc_info=True)


@router.options("/performance/eval-stream")
async def eval_stream_options():
    """Handle CORS preflight for the SSE endpoint."""
    return Response(headers=SSE_CORS_HEADERS)


@router.get("/performance/eval-stream")
async def skill_eval_stream():
    """SSE endpoint for live skill evaluation events.

    Streams events broadcast by the background evaluation scheduler
    (SkillEvaluationScheduler). Events include:
    - skill_eval_completed: evaluation finished with results
    - skill_eval_error: evaluation failed

    Frontend connects with EventSource and shows toasts.
    """
    return StreamingResponse(
        _eval_event_generator(),
        media_type="text/event-stream",
        headers=SSE_CORS_HEADERS,
    )
