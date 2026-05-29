"""Main API router."""

from fastapi import APIRouter

from .projects import router as projects_router

api_router = APIRouter()

# Include all route modules
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])

# Future routes will be added here:
# api_router.include_router(ideas_router, prefix="/projects/{project_id}/ideas", tags=["ideas"])
# api_router.include_router(runs_router, prefix="/projects/{project_id}/runs", tags=["runs"])
# api_router.include_router(papers_router, prefix="/projects/{project_id}/papers", tags=["papers"])
# api_router.include_router(skills_router, prefix="/projects/{project_id}/skills", tags=["skills"])
# api_router.include_router(reports_router, prefix="/projects/{project_id}/reports", tags=["reports"])
# api_router.include_router(wiki_router, prefix="/projects/{project_id}/wiki", tags=["wiki"])
# api_router.include_router(idle_router, prefix="/projects/{project_id}/idle", tags=["idle"])
# api_router.include_router(approval_router, prefix="/projects/{project_id}/approvals", tags=["approvals"])
# api_router.include_router(audit_router, prefix="/projects/{project_id}/audit", tags=["audit"])
