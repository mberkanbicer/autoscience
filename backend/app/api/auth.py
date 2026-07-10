"""JWT and OAuth authentication endpoints."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.dependencies.auth import get_current_user, resolve_user
from app.models.collaboration import User
from app.schemas.collaboration import UserResponse
from app.services.auth_service import create_access_token
from app.services.oauth_service import build_authorize_url, exchange_code, list_configured_providers

logger = structlog.get_logger()

router = APIRouter()


class TokenRequest(BaseModel):
    email: str = Field(..., min_length=3)
    display_name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class OAuthAuthorizeResponse(BaseModel):
    provider: str
    url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    code: str = Field(..., min_length=1)
    state: str | None = None


async def _token_response(db: AsyncSession, user: User) -> TokenResponse:
    token = create_access_token(user.id, user.email)
    await db.commit()
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            created_at=user.created_at,
        ),
    )


@router.post("/token", response_model=TokenResponse)
async def issue_token(
    data: TokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Issue a JWT for the given email (MVP login — no password)."""
    user = await resolve_user(db, email=data.email, display_name=data.display_name)
    return await _token_response(db, user)


@router.get("/me", response_model=UserResponse)
async def auth_me(user: Annotated[User, Depends(get_current_user)]):
    """Current authenticated user."""
    return user


@router.get("/oauth/providers")
async def oauth_providers():
    """List OAuth providers configured via environment variables."""
    return {"providers": list_configured_providers()}


@router.get("/oauth/{provider}/authorize", response_model=OAuthAuthorizeResponse)
async def oauth_authorize(provider: str):
    """Return the provider authorization URL for the frontend redirect flow."""
    try:
        url, state = build_authorize_url(provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OAuthAuthorizeResponse(provider=provider, url=url, state=state)


@router.post("/oauth/{provider}/callback", response_model=TokenResponse)
async def oauth_callback(
    provider: str,
    data: OAuthCallbackRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Exchange OAuth authorization code for a JWT."""
    try:
        profile = await exchange_code(provider, data.code)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=f"OAuth exchange failed: {exc}") from exc
    except Exception as exc:
        logger.error("oauth_exchange_unexpected", provider=provider, error=str(exc))
        raise HTTPException(status_code=502, detail="OAuth exchange failed unexpectedly") from exc

    user = await resolve_user(
        db,
        email=profile["email"],
        display_name=profile.get("display_name"),
    )
    return await _token_response(db, user)
