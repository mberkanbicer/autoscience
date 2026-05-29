"""Main API endpoint for research operations."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..services.orchestrator import ResearchOrchestrator
from ..llm.router import LLMRouter, create_default_router
from ..connectors.manager import ConnectorManager, create_default_manager
from ..config import get_settings

router = APIRouter()

# Initialize components (would be done in app startup in production)
settings = get_settings()


def get_llm_router() -> LLMRouter:
    """Get LLM router instance."""
    return create_default_router(
        openai_api_key=settings.openai_api_key,
        anthropic_api_key=settings.anthropic_api_key,
        local_base_url=settings.local_llm_base_url,
        local_model=settings.local_llm_model,
        default_provider=settings.default_llm_provider,
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
    db: AsyncSession = Depends(get_db),
):
    """Start a research run."""
    orchestrator = get_orchestrator(db)

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
