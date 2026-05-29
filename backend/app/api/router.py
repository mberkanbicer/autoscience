"""Main API router."""

from fastapi import APIRouter

from .projects import router as projects_router
from .ideas import router as ideas_router
from .runs import router as runs_router
from .papers import router as papers_router
from .skills import router as skills_router
from .questions import router as questions_router
from .reports import router as reports_router

api_router = APIRouter()

# Include all route modules
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(ideas_router, prefix="/ideas", tags=["ideas"])
api_router.include_router(runs_router, prefix="/runs", tags=["runs"])
api_router.include_router(papers_router, prefix="/papers", tags=["papers"])
api_router.include_router(skills_router, prefix="/skills", tags=["skills"])
api_router.include_router(questions_router, prefix="", tags=["questions"])
api_router.include_router(reports_router, prefix="", tags=["reports"])
