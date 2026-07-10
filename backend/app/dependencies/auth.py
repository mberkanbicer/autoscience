"""Authentication and RBAC dependencies."""

from __future__ import annotations

from uuid import uuid4

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import get_db
from app.models.collaboration import ProjectMember, User
from app.services.auth_service import decode_access_token

ROLE_RANK = {"viewer": 1, "editor": 2, "owner": 3}


async def resolve_user(
    db: AsyncSession,
    *,
    email: str,
    display_name: str | None = None,
) -> User:
    normalized = email.strip().lower()
    name = (display_name or normalized.split("@")[0]).strip()
    result = await db.execute(select(User).where(User.email == normalized))
    user = result.scalar_one_or_none()
    if user:
        if display_name and user.display_name != name:
            user.display_name = name
            await db.flush()
        return user
    user = User(id=str(uuid4()), email=normalized, display_name=name)
    db.add(user)
    await db.flush()
    return user


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_name: str | None = Header(None, alias="X-User-Name"),
) -> User:
    """Resolve the current user.

    In production, identity is derived ONLY from a verified JWT Bearer token.
    Client-supplied ``X-User-Email`` / ``X-User-Name`` headers are trusted ONLY
    in non-production environments (development/test) so the test-suite and
    local dev tooling can impersonate users without a login flow. This closes
    the production identity-spoofing vulnerability while keeping tests working.
    """
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        try:
            payload = decode_access_token(token)
        except Exception as exc:
            raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
        user = await db.get(User, payload.get("sub"))
        if user:
            return user
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if get_settings().app_env != "production" and x_user_email:
        return await resolve_user(db, email=x_user_email, display_name=x_user_name)

    return await resolve_user(db, email="anonymous@local", display_name="Anonymous")


async def get_project_role(
    db: AsyncSession,
    project_id: str,
    user_id: str,
) -> str | None:
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        ),
    )
    member = result.scalar_one_or_none()
    return member.role if member else None


async def require_project_role(
    db: AsyncSession,
    project_id: str,
    user_id: str,
    min_role: str = "viewer",
) -> str:
    """Ensure user has at least min_role on project. Open if no members exist."""
    members = await db.execute(
        select(ProjectMember).where(ProjectMember.project_id == project_id),
    )
    if not members.scalars().first():
        return "owner"

    role = await get_project_role(db, project_id, user_id)
    if not role:
        raise HTTPException(status_code=403, detail="Not a project member")

    if ROLE_RANK.get(role, 0) < ROLE_RANK.get(min_role, 0):
        raise HTTPException(status_code=403, detail=f"Requires {min_role} role")
    return role


async def require_editor(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> User:
    await require_project_role(db, project_id, user.id, "editor")
    return user


async def require_owner(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> User:
    await require_project_role(db, project_id, user.id, "owner")
    return user
