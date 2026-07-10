"""API key authentication middleware."""

import structlog
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED

logger = structlog.get_logger()

# Endpoints that don't require authentication
PUBLIC_ENDPOINTS = {"/api/v1/health", "/health", "/docs", "/redoc", "/openapi.json"}


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce API key authentication."""

    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints and static files
        if request.url.path in PUBLIC_ENDPOINTS or request.url.path.startswith("/_next"):
            return await call_next(request)

        # Skip auth in development mode
        from app.config import get_settings

        if get_settings().app_env == "development" and not get_settings().api_key:
            return await call_next(request)

        # Check for API key in header
        api_key = request.headers.get("x-api-key")
        expected_key = get_settings().api_key

        if not expected_key or api_key != expected_key:
            logger.warning("unauthorized_access", path=request.url.path, client_ip=request.client.host if request.client else "unknown")
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="API key required or invalid",
            )

        response = await call_next(request)
        return response
