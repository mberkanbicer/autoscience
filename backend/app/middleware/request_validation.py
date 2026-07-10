"""Request validation middleware for security."""

import structlog
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_413_CONTENT_TOO_LARGE

logger = structlog.get_logger()

MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate request size and other constraints."""

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")

        if content_length and int(content_length) > MAX_BODY_SIZE:
            logger.warning(
                "request_too_large",
                path=request.url.path,
                content_length=content_length,
            )
            raise HTTPException(
                status_code=HTTP_413_CONTENT_TOO_LARGE,
                detail="Request body too large",
            )

        return await call_next(request)
