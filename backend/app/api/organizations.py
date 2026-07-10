"""Organization API endpoints — multi-tenancy project isolation."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.models.collaboration import User
from app.models.organization import Organization, OrganizationMember
from app.models.project import Project
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationMemberResponse,
    OrganizationResponse,
    OrganizationUpdate,
)

router = APIRouter()


async def _ensure_org_role(
    db: AsyncSession,
    org_id: str,
    user_id: str,
    min_role: str = "member",
) -> OrganizationMember:
    """Verify user has at least min_role in the organization."""
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
        ),
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    role_rank = {"viewer": 1, "member": 2, "admin": 3, "owner": 4}
    if role_rank.get(member.role, 0) < role_rank.get(min_role, 0):
        raise HTTPException(
            status_code=403,
            detail=f"Requires {min_role} role in organization (current: {member.role})",
        )
    return member


@router.post("", response_model=OrganizationResponse, status_code=201)
async def create_organization(
    data: OrganizationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Organization:
    """Create a new organization. The creator becomes the owner."""
    # Check slug uniqueness
    existing = await db.execute(
        select(Organization).where(Organization.slug == data.slug),
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Organization slug already exists")

    org = Organization(
        id=str(uuid4()),
        name=data.name,
        slug=data.slug,
        description=data.description,
        domain=data.domain,
        max_projects=data.max_projects,
        max_users=data.max_users,
    )
    db.add(org)
    await db.flush()

    # Creator becomes owner
    db.add(
        OrganizationMember(
            id=str(uuid4()),
            organization_id=org.id,
            user_id=user.id,
            role="owner",
        ),
    )
    await db.commit()
    await db.refresh(org)
    return org


@router.get("", response_model=list[OrganizationResponse])
async def list_organizations(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[Organization]:
    """List organizations the current user is a member of."""
    result = await db.execute(
        select(Organization).join(
            OrganizationMember,
            OrganizationMember.organization_id == Organization.id,
        ).where(
            OrganizationMember.user_id == user.id,
            OrganizationMember.is_active == True,
        ),
    )
    return result.scalars().all()


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Organization:
    """Get organization details (requires membership)."""
    await _ensure_org_role(db, org_id, user.id, "viewer")
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    data: OrganizationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Organization:
    """Update organization settings (admin+ only)."""
    await _ensure_org_role(db, org_id, user.id, "admin")
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)

    await db.commit()
    await db.refresh(org)
    return org


@router.delete("/{org_id}", status_code=204)
async def delete_organization(
    org_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete an organization (owner only). Projects are orphaned (SET NULL)."""
    await _ensure_org_role(db, org_id, user.id, "owner")
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    await db.delete(org)
    await db.commit()


@router.get("/{org_id}/members", response_model=list[OrganizationMemberResponse])
async def list_org_members(
    org_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """List all members of an organization (requires membership)."""
    await _ensure_org_role(db, org_id, user.id, "viewer")
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
        ).order_by(OrganizationMember.created_at),
    )
    return result.scalars().all()


@router.post("/{org_id}/members", response_model=OrganizationMemberResponse, status_code=201)
async def add_org_member(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    org_id: str,
    email: Annotated[str, Query()],
    role: Annotated[str, Query(pattern="^(viewer|member|admin|owner)$")] = "member",
):
    """Add a user to the organization by email (admin+ only)."""
    await _ensure_org_role(db, org_id, user.id, "admin")

    # Resolve user by email
    from app.dependencies.auth import resolve_user

    target_user = await resolve_user(db, email=email)

    # Check if already a member
    existing = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == target_user.id,
        ),
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User is already a member of this organization")

    # Check org user limit
    org_result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    member_count = await db.execute(
        select(func.count(OrganizationMember.id)).where(
            OrganizationMember.organization_id == org_id,
        ),
    )
    if member_count.scalar() >= org.max_users:
        raise HTTPException(status_code=403, detail="Organization has reached its user limit")

    member = OrganizationMember(
        id=str(uuid4()),
        organization_id=org_id,
        user_id=target_user.id,
        role=role,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/{org_id}/members/{member_id}", status_code=204)
async def remove_org_member(
    org_id: str,
    member_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Remove a member from the organization (admin+ only, or self-removal)."""
    # Self-removal is always allowed
    caller_role = None
    try:
        caller = await _ensure_org_role(db, org_id, user.id, "member")
        caller_role = caller.role
    except HTTPException:
        pass

    member_result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == org_id,
        ),
    )
    member = member_result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Allow self-removal or admin+ action
    if member.user_id != user.id and caller_role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Requires admin role or self-removal")

    await db.delete(member)
    await db.commit()


@router.get("/{org_id}/stats")
async def get_org_stats(
    org_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get organization statistics (requires membership)."""
    await _ensure_org_role(db, org_id, user.id, "viewer")

    # Member count
    member_count = await db.execute(
        select(func.count(OrganizationMember.id)).where(
            OrganizationMember.organization_id == org_id,
        ),
    )

    # Project count
    project_count = await db.execute(
        select(func.count(Project.id)).where(Project.organization_id == org_id),
    )

    # Org info
    org_result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return {
        "organization_id": org_id,
        "name": org.name,
        "slug": org.slug,
        "total_members": member_count.scalar() or 0,
        "total_projects": project_count.scalar() or 0,
        "max_projects": org.max_projects,
        "max_users": org.max_users,
    }
