"""Main API router."""

from fastapi import APIRouter

from .approvals import router as approvals_router
from .auth import router as auth_router
from .collaboration import router as collaboration_router
from .connectors import router as connectors_router
from .datasets import router as datasets_router
from .ideas import router as ideas_router
from .manuscripts import router as manuscripts_router
from .organizations import router as organizations_router
from .papers import router as papers_router
from .projects import router as projects_router
from .questions import router as questions_router
from .reports import router as reports_router
from .research import router as research_router
from .runs import router as runs_router
from .sandbox_analysis import router as sandbox_analysis_router
from .search import router as search_router
from .skills import router as skills_router
from .user_activity import router as activity_router
from .wiki import router as wiki_router

api_router = APIRouter()


@api_router.get("/llm/status")
async def llm_status():
    """Check if any LLM provider is configured via headers."""
    return {"configured": False, "message": "Set an API key in Settings to enable AI-powered analysis"}


@api_router.get("/scheduler/status")
async def scheduler_status():
    """Get idle cycle scheduler status."""
    from app.services.idle_scheduler import get_scheduler_status
    return get_scheduler_status()


@api_router.get("/health")
async def health_check():
    """Aggregated health check for DB, Redis, LLM providers, and connectors."""
    from app.config import get_settings
    from app.connectors.manager import create_default_manager
    from app.database import async_session_factory
    from app.services.health_service import HealthService

    settings = get_settings()

    # Build a lightweight connector manager with the configured API keys
    connector_manager = create_default_manager(
        openalex_email=settings.unpaywall_email,
        semantic_scholar_api_key=settings.semantic_scholar_api_key,
        pubmed_api_key="",
        core_api_key=settings.core_api_key,
        unpaywall_email=settings.unpaywall_email,
        searxng_url=settings.searxng_url,
        firecrawl_api_key=settings.firecrawl_api_key,
    )

    service = HealthService(
        db_session_factory=async_session_factory,
        redis_url=settings.redis_url,
        connector_manager=connector_manager,
    )

    result = await service.check_all()
    return result


api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(ideas_router, prefix="/ideas", tags=["ideas"])
api_router.include_router(runs_router, prefix="/runs", tags=["runs"])
api_router.include_router(papers_router, prefix="/papers", tags=["papers"])
api_router.include_router(skills_router, prefix="/skills", tags=["skills"])
api_router.include_router(questions_router, prefix="/questions", tags=["questions"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(research_router, prefix="/research", tags=["research"])
api_router.include_router(search_router, prefix="/search", tags=["search"])
api_router.include_router(datasets_router, prefix="/datasets", tags=["datasets"])
api_router.include_router(activity_router, prefix="/activity", tags=["activity"])
api_router.include_router(approvals_router, prefix="/approvals", tags=["approvals"])
api_router.include_router(wiki_router, prefix="/wiki", tags=["wiki"])
api_router.include_router(manuscripts_router, prefix="/manuscripts", tags=["manuscripts"])
api_router.include_router(connectors_router, prefix="/connectors", tags=["connectors"])
api_router.include_router(collaboration_router, prefix="/collaboration", tags=["collaboration"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(organizations_router, prefix="/organizations", tags=["organizations"])
api_router.include_router(sandbox_analysis_router, prefix="/sandbox", tags=["sandbox"])
