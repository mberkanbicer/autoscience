"""Main API endpoint for research operations."""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..dependencies import get_db
from ..services.orchestrator import ResearchOrchestrator
from ..llm.router import LLMRouter, create_default_router
from ..connectors.manager import ConnectorManager, create_default_manager
from ..config import get_settings

router = APIRouter()

# Initialize components (would be done in app startup in production)
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
    # Use header values if provided, otherwise fall back to env
    or_key = openrouter_api_key or settings.openrouter_api_key
    oa_key = openai_api_key or settings.openai_api_key
    an_key = anthropic_api_key or settings.anthropic_api_key
    
    # Determine default provider
    provider = default_provider or settings.default_llm_provider
    
    # If we have an API key from headers, use that provider as default
    if or_key and not oa_key and not an_key:
        provider = 'openrouter'
    elif oa_key and not or_key and not an_key:
        provider = 'openai'
    elif an_key and not or_key and not oa_key:
        provider = 'anthropic'
    
    return create_default_router(
        openai_api_key=oa_key,
        openai_default_model=openai_model or settings.openai_default_model,
        anthropic_api_key=an_key,
        anthropic_default_model=anthropic_model or settings.anthropic_default_model,
        openrouter_api_key=or_key,
        openrouter_default_model=openrouter_model or settings.openrouter_default_model,
        openrouter_base_url=settings.openrouter_base_url,
        local_base_url=settings.local_llm_base_url,
        local_model=settings.local_llm_model,
        llamacpp_base_url=settings.llamacpp_base_url,
        llamacpp_model=settings.llamacpp_model,
        default_provider=provider,
    )


def get_connector_manager() -> ConnectorManager:
    """Get connector manager instance."""
    return create_default_manager(
        openalex_email=settings.unpaywall_email,
        semantic_scholar_api_key=settings.semantic_scholar_api_key,
    )


def get_orchestrator(db: AsyncSession) -> ResearchOrchestrator:
    """Get orchestrator instance."""
    return ResearchOrchestrator(
        db=db,
        llm_router=get_llm_router(),
        connector_manager=get_connector_manager(),
    )


@router.post("/research/run")
async def start_research_run(
    project_id: str,
    idea: str,
    run_type: str = "user_directed",
    flexibility: float = 0.6,
    x_openrouter_api_key: Optional[str] = Header(None),
    x_openrouter_model: Optional[str] = Header(None),
    x_openai_api_key: Optional[str] = Header(None),
    x_openai_model: Optional[str] = Header(None),
    x_anthropic_api_key: Optional[str] = Header(None),
    x_anthropic_model: Optional[str] = Header(None),
    x_default_provider: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Start a research run."""
    llm_router = get_llm_router(
        openrouter_api_key=x_openrouter_api_key,
        openrouter_model=x_openrouter_model,
        openai_api_key=x_openai_api_key,
        openai_model=x_openai_model,
        anthropic_api_key=x_anthropic_api_key,
        anthropic_model=x_anthropic_model,
        default_provider=x_default_provider,
    )
    
    orchestrator = ResearchOrchestrator(
        db=db,
        llm_router=llm_router,
        connector_manager=get_connector_manager(),
    )

    try:
        state = await orchestrator.run_research(
            project_id=project_id,
            idea_text=idea,
            run_type=run_type,
            flexibility=flexibility,
        )

        return {
            "success": True,
            "run_id": state.run_id,
            "papers_found": len(state.papers),
            "conflicts_found": len(state.conflicts),
            "questions_generated": len(state.questions),
            "hypotheses_formed": len(state.hypotheses),
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research/idle")
async def start_idle_cycle(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Start an idle cognition cycle."""
    orchestrator = get_orchestrator(db)

    try:
        result = await orchestrator.run_idle_cycle(project_id)
        return {"success": True, **result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
