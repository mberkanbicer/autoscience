"""Integration tests for the Organization multi-tenancy model."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization, OrganizationMember
from app.models.collaboration import User


@pytest.mark.asyncio
async def test_create_organization(db_session: AsyncSession):
    """Creating an Organization persists it with the correct fields."""
    org = Organization(
        name="Test Research Lab",
        slug="test-lab",
        description="A lab for testing multi-tenancy",
        domain="testlab.org",
        max_projects=25,
        max_users=100,
    )
    db_session.add(org)
    await db_session.commit()

    assert org.id is not None
    assert org.name == "Test Research Lab"
    assert org.slug == "test-lab"
    assert org.description == "A lab for testing multi-tenancy"
    assert org.domain == "testlab.org"
    assert org.max_projects == 25
    assert org.max_users == 100
    assert org.is_active is True
    assert org.created_at is not None


@pytest.mark.asyncio
async def test_organization_slug_uniqueness(db_session: AsyncSession):
    """Organization slugs must be unique."""
    org1 = Organization(name="Lab One", slug="unique-lab")
    db_session.add(org1)
    await db_session.commit()

    org2 = Organization(name="Lab Two", slug="unique-lab")
    db_session.add(org2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_create_organization_member(db_session: AsyncSession):
    """Creating an OrganizationMember with valid org and user IDs works."""
    org = Organization(name="Member Test Lab", slug="member-test")
    db_session.add(org)
    await db_session.commit()

    user = User(
        email="researcher@testlab.org",
        display_name="Dr. Researcher",
    )
    db_session.add(user)
    await db_session.commit()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role="admin",
    )
    db_session.add(member)
    await db_session.commit()

    assert member.id is not None
    assert member.organization_id == org.id
    assert member.user_id == user.id
    assert member.role == "admin"
    assert member.is_active is True

    # Verify relationship loading
    assert member.organization is not None
    assert member.organization.name == "Member Test Lab"


@pytest.mark.asyncio
async def test_organization_member_unique_constraint(db_session: AsyncSession):
    """An (organization_id, user_id) pair must be unique."""
    org = Organization(name="Unique Member Lab", slug="unique-member")
    db_session.add(org)
    user = User(email="unique@test.org", display_name="Unique User")
    db_session.add(user)
    await db_session.commit()

    member1 = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role="member",
    )
    db_session.add(member1)
    await db_session.commit()

    member2 = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role="admin",
    )
    db_session.add(member2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_organization_cascade_delete(db_session: AsyncSession):
    """Deleting an Organization cascades to its members."""
    org = Organization(name="Cascade Test Org", slug="cascade-test")
    db_session.add(org)
    user = User(email="cascade@test.org", display_name="Cascade User")
    db_session.add(user)
    await db_session.commit()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role="viewer",
    )
    db_session.add(member)
    await db_session.commit()

    # Delete the organization
    await db_session.delete(org)
    await db_session.commit()

    # Members should be gone
    result = await db_session.execute(
        select(OrganizationMember).where(OrganizationMember.organization_id == org.id)
    )
    assert result.scalar_one_or_none() is None, "Members should cascade-delete"


@pytest.mark.asyncio
async def test_organization_member_roles(db_session: AsyncSession):
    """OrganizationMember supports different roles (owner, admin, member, viewer)."""
    org = Organization(name="Roles Lab", slug="roles-lab")
    db_session.add(org)

    users = []
    for role in ("owner", "admin", "member", "viewer"):
        user = User(
            email=f"{role}@roles.org",
            display_name=f"{role.title()} User",
        )
        db_session.add(user)
        await db_session.flush()
        users.append(user)

        member = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role=role,
        )
        db_session.add(member)
    await db_session.commit()

    # Verify all roles are stored correctly
    result = await db_session.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org.id
        ).order_by(OrganizationMember.id)
    )
    members = result.scalars().all()
    assert len(members) == 4
    stored_roles = {m.role for m in members}
    assert stored_roles == {"owner", "admin", "member", "viewer"}


@pytest.mark.asyncio
async def test_organization_default_values(db_session: AsyncSession):
    """Organization uses sensible defaults for optional fields."""
    org = Organization(name="Defaults Lab", slug="defaults-lab")
    db_session.add(org)
    await db_session.commit()

    assert org.max_projects == 10
    assert org.max_users == 25
    assert org.is_active is True
    assert org.settings is None
