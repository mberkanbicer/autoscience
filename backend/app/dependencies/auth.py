"""Authentication and RBAC dependencies."""

from __future__ import annotations

from uuid import uuid4

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.collaboration import ProjectMember, User
from app.services.auth_service import decode_access_token

ROLE_RANK = {"viewer": 1, "editor": 2, "owner": 3}


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
) -> User:
    """Resolve the current user from a verified JWT Bearer token.

    Identity is derived ONLY from the signed JWT. Client-supplied headers
    (previously ``X-User-Email``) are never trusted, which prevented identity
    spoofing. Requests without a valid token fall back to a fixed system
    anonymous user so local development without a login flow still works;
    unauthenticated access to protected resources must be enforced via JWT in
    production deployments.
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
