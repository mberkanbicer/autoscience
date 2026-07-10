"""Main API endpoint for research operations."""

import asyncio
from typing import Annotated, Optional

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.connectors.manager import ConnectorManager
from app.database import async_session_factory
from app.dependencies import get_connector_manager, get_db
from app.dependencies.auth import get_current_user, require_project_role
from app.llm.router import LLMRouter, create_default_router
from app.models.collaboration import User
from app.schemas.research_run import ResearchRunCreate
from app.schemas.validation import StartResearchRunRequest
from app.services.event_stream import EventBroadcaster
from app.services.orchestrator import ResearchOrchestrator
from app.services.research_run_service import ResearchRunService

logger = structlog.get_logger()

router = APIRouter()

settings = get_settings()


def get_llm_router(
    openrouter_api_key: str | None = None,
    openrouter_model: str | None = None,
    openai_api_key: str | None = None,
    openai_model: str | None = None,
    anthropic_api_key: str | None = None,
    anthropic_model: str | None = None,
    default_provider: str | None = None,
) -> LLMRouter:
    """Get LLM router instance with API keys from headers or env."""
    or_key = (openrouter_api_key or None) or settings.openrouter_api_key
    oa_key = (openai_api_key or None) or settings.openai_api_key
    an_key = (anthropic_api_key or None) or settings.anthropic_api_key

    provider = default_provider or settings.default_llm_provider
    if or_key and not oa_key and not an_key:
        provider = "openrouter"
    elif oa_key and not or_key and not an_key:
        provider = "openai"
    elif an_key and not or_key and not oa_key:
        provider = "anthropic"

    logger.info("llm_router_created", provider=provider, has_openrouter=bool(or_key), has_openai=bool(oa_key), has_anthropic=bool(an_key))

    return create_default_router(
        openai_api_key=oa_key,
        anthropic_api_key=an_key,
        openrouter_api_key=or_key,
        openrouter_default_model=openrouter_model or settings.openrouter_default_model,
        openrouter_base_url=settings.openrouter_base_url,
        local_base_url=settings.local_llm_base_url,
        local_model=settings.local_llm_model,
        llamacpp_base_url=settings.llamacpp_base_url,
        llamacpp_model=settings.llamacpp_model,
        default_provider=provider,
    )


async def _run_workflow_background(
    run_id: str,
    project_id: str,
    idea_text: str,
    run_type: str,
    flexibility: float,
    llm_router: LLMRouter,
    connector_manager: ConnectorManager,
    event_broadcaster: EventBroadcaster | None = None,
) -> None:
    """Run the research workflow in a background task with its own DB session."""
    try:
        async with async_session_factory() as db:
            orchestrator = ResearchOrchestrator(
                db=db,
                llm_router=llm_router,
                connector_manager=connector_manager,
                event_broadcaster=event_broadcaster,
            )

            # Mark run as started and commit so frontend can see it
            run_service = ResearchRunService(db)
            await run_service.start_run(run_id)
            await db.commit()

            await orchestrator.run_research(
                project_id=project_id,
                idea_text=idea_text,
                run_type=run_type,
                flexibility=flexibility,
                existing_run_id=run_id,
            )

            await db.commit()
            logger.info("background_run_completed", run_id=run_id)

    except asyncio.CancelledError:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logger.error("background_run_failed", run_id=run_id, error=str(e))
        # Try to mark the run as failed
        try:
            async with async_session_factory() as db2:
                run_service = ResearchRunService(db2)
                await run_service.fail_run(run_id, str(e))
                await db2.commit()
        except ImportError:
            logger.error("failed_to_mark_failed", error="Redis not available")
        except SQLAlchemyError as e2:
            logger.error("failed_to_mark_failed_db_error", error=str(e2))
        except Exception as e2:
            logger.error("failed_to_mark_failed", error=str(e2))


@router.post("/run")
async def start_research_run(
    request: StartResearchRunRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    x_openrouter_api_key: Annotated[str | None, Header()] = None,
    x_openrouter_model: Annotated[str | None, Header()] = None,
    x_openai_api_key: Annotated[str | None, Header()] = None,
    x_openai_model: Annotated[str | None, Header()] = None,
    x_anthropic_api_key: Annotated[str | None, Header()] = None,
    x_anthropic_model: Annotated[str | None, Header()] = None,
    x_default_provider: Annotated[str | None, Header()] = None,
):
    """Start a research run (non-blocking).

    Returns immediately with run_id. The workflow runs in the background.
    Subscribe to GET /api/v1/search/stream/{run_id} for live events.
    Poll GET /api/v1/runs/{run_id} for completion status.
    """
    await require_project_role(db, request.project_id, user.id, "editor")
    llm_router = get_llm_router(
        openrouter_api_key=x_openrouter_api_key,
        openrouter_model=x_openrouter_model,
        openai_api_key=x_openai_api_key,
        openai_model=x_openai_model,
        anthropic_api_key=x_anthropic_api_key,
        anthropic_model=x_anthropic_model,
        default_provider=x_default_provider,
    )
    connector_manager = get_connector_manager()

    # Create the idea and run record first (in the request's DB session)
    from app.services.idea_ledger_service import IdeaLedgerService
    idea_ledger = IdeaLedgerService(db)
    idea_obj = await idea_ledger.create_idea(
        project_id=request.project_id,
        text=request.idea,
        origin="user_prompt",
        flexibility=request.flexibility,
    )

    run_service = ResearchRunService(db)
    run = await run_service.create_run(
        project_id=request.project_id,
        data=ResearchRunCreate(
            idea_id=idea_obj.id,
            run_type=request.run_type,
        ),
    )
    await db.commit()

    # Set up event broadcaster for live streaming
    try:
        import redis
        import redis.asyncio as aioredis
        redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_keepalive=True,
            socket_timeout=None,
        )
        event_broadcaster = EventBroadcaster(redis_client)
    except (ImportError, redis.ConnectionError):
        event_broadcaster = None
        logger.warning("redis_unavailable", note="Redis not reachable or client not installed, events will not be streamed")

    # Start workflow in background
    asyncio.create_task(
        _run_workflow_background(
            run_id=run.id,
            project_id=request.project_id,
            idea_text=request.idea,
            run_type=request.run_type,
            flexibility=request.flexibility,
            llm_router=llm_router,
            connector_manager=connector_manager,
            event_broadcaster=event_broadcaster,
        ),
    )

    return {
        "success": True,
        "run_id": run.id,
        "idea_id": idea_obj.id,
        "status": "started",
        "stream_url": f"/api/v1/search/stream/{run.id}",
    }


@router.post("/idle")
async def start_idle_cycle(
    project_id: Annotated[str, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Start an idle cognition cycle."""
    await require_project_role(db, project_id, user.id, "editor")
    llm_router = get_llm_router()
    orchestrator = ResearchOrchestrator(
        db=db,
        llm_router=llm_router,
        connector_manager=get_connector_manager(),
    )

    try:
        result = await orchestrator.run_idle_cycle(project_id)
        return {"success": True, **result}

    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error("idle_cycle_unexpected", error=str(e))
        raise HTTPException(status_code=500, detail="Internal error during idle cycle")
