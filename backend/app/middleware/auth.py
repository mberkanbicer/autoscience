"""API key authentication middleware."""

import structlog
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED

from app.config import get_settings

logger = structlog.get_logger()

# Endpoints that don't require authentication
PUBLIC_ENDPOINTS = {"/api/v1/health", "/health", "/docs", "/redoc", "/openapi.json"}
# Auth issuance endpoints are public so clients can obtain a JWT.
PUBLIC_PREFIXES = ("/api/v1/auth",)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing an API key or Bearer token on protected routes.

    The coarse API-key gate is enforced only when ``api_key`` is configured.
    When no API key is set, per-route JWT authentication (via dependencies)
    remains the source of truth. A valid Bearer token always passes this gate;
    fine-grained authorization is then handled by route dependencies.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if (
            path in PUBLIC_ENDPOINTS
            or path.startswith("/_next")
            or any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)
        ):
            return await call_next(request)

        settings = get_settings()
        expected_key = settings.api_key

        # No API key configured: rely on per-route JWT auth.
        if not expected_key:
            return await call_next(request)

        authorization = request.headers.get("authorization")
        if authorization and authorization.lower().startswith("bearer "):
            return await call_next(request)

        api_key = request.headers.get("x-api-key")
        if api_key and api_key == expected_key:
            return await call_next(request)

        logger.warning(
            "unauthorized_access",
            path=path,
            client_ip=request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API key or Bearer token required",
        )

        response = await call_next(request)
        return response
