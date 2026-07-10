"""JWT token issuance and validation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import jwt

from app.config import get_settings


def create_access_token(user_id: str, email: str) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(hours=settings.jwt_expire_hours)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, settings.app_secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.app_secret_key, algorithms=["HS256"])
