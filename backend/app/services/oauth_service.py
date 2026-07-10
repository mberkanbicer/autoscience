"""OAuth2 login for Google and GitHub."""

from __future__ import annotations

import secrets
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import get_settings

PROVIDERS = ("google", "github")


def list_configured_providers() -> list[str]:
    settings = get_settings()
    configured: list[str] = []
    if settings.google_oauth_client_id and settings.google_oauth_client_secret:
        configured.append("google")
    if settings.github_oauth_client_id and settings.github_oauth_client_secret:
        configured.append("github")
    return configured


def build_authorize_url(provider: str, *, state: str | None = None) -> tuple[str, str]:
    settings = get_settings()
    state = state or secrets.token_urlsafe(16)
    redirect_uri = settings.oauth_redirect_uri

    if provider == "google":
        if not settings.google_oauth_client_id:
            raise ValueError("Google OAuth is not configured")
        params = {
            "client_id": settings.google_oauth_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "online",
            "prompt": "select_account",
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}", state

    if provider == "github":
        if not settings.github_oauth_client_id:
            raise ValueError("GitHub OAuth is not configured")
        params = {
            "client_id": settings.github_oauth_client_id,
            "redirect_uri": redirect_uri,
            "scope": "read:user user:email",
            "state": state,
        }
        return f"https://github.com/login/oauth/authorize?{urlencode(params)}", state

    raise ValueError(f"Unsupported OAuth provider: {provider}")


async def exchange_code(provider: str, code: str) -> dict[str, str]:
    """Exchange authorization code for user email and display name."""
    settings = get_settings()
    redirect_uri = settings.oauth_redirect_uri

    async with httpx.AsyncClient(timeout=20.0) as client:
        if provider == "google":
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.google_oauth_client_id,
                    "client_secret": settings.google_oauth_client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            token_resp.raise_for_status()
            access_token = token_resp.json()["access_token"]
            profile_resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            profile_resp.raise_for_status()
            profile: dict[str, Any] = profile_resp.json()
            return {
                "email": profile["email"],
                "display_name": profile.get("name") or profile["email"].split("@")[0],
            }

        if provider == "github":
            token_resp = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "code": code,
                    "client_id": settings.github_oauth_client_id,
                    "client_secret": settings.github_oauth_client_secret,
                    "redirect_uri": redirect_uri,
                },
            )
            token_resp.raise_for_status()
            access_token = token_resp.json()["access_token"]
            user_resp = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            user_resp.raise_for_status()
            user: dict[str, Any] = user_resp.json()
            email = user.get("email")
            if not email:
                emails_resp = await client.get(
                    "https://api.github.com/user/emails",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github+json",
                    },
                )
                emails_resp.raise_for_status()
                emails = emails_resp.json()
                primary = next((e for e in emails if e.get("primary")), emails[0] if emails else None)
                email = primary["email"] if primary else f"{user['login']}@users.noreply.github.com"
            return {
                "email": email,
                "display_name": user.get("name") or user.get("login") or email.split("@")[0],
            }

    raise ValueError(f"Unsupported OAuth provider: {provider}")
