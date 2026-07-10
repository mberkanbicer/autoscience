"""Collaboration API — members, comments, reviews, activity."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.dependencies.auth import get_current_user, require_project_role, resolve_user
from app.models.collaboration import Comment, ProjectMember, ReviewProposal, User
from app.schemas.collaboration import (
    ActivityItem,
    CommentCreate,
    CommentResponse,
    MemberCreate,
    MemberResponse,
    PeerReviewSimulation,
    ReviewNotification,
    ReviewProposalCreate,
    ReviewProposalResponse,
    ReviewProposalUpdate,
    UserResponse,
)
from app.services.activity_feed_service import ActivityFeedService
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/users/me", response_model=UserResponse)
async def get_current_user_profile(user: Annotated[User, Depends(get_current_user)]):
    return user


@router.get("/members", response_model=list[MemberResponse])
async def list_members(
    project_id: Annotated[str, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ProjectMember, User)
        .join(User, User.id == ProjectMember.user_id)
        .where(ProjectMember.project_id == project_id),
    )
    return [
        MemberResponse(
            id=member.id,
            project_id=member.project_id,
            user_id=member.user_id,
            role=member.role,
            email=user.email,
            display_name=user.display_name,
            created_at=member.created_at,
        )
        for member, user in result.all()
    ]


@router.post("/members", response_model=MemberResponse, status_code=201)
async def add_member(
    data: MemberCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_user)],
):
    members_result = await db.execute(
        select(ProjectMember).where(ProjectMember.project_id == data.project_id),
    )
    existing_members = list(members_result.scalars().all())
    role = data.role
    if existing_members:
        await require_project_role(db, data.project_id, actor.id, "owner")
    else:
        role = "owner"

    target = await resolve_user(db, email=data.email, display_name=data.display_name)
    dup = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == data.project_id,
            ProjectMember.user_id == target.id,
        ),
    )
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User is already a member")

    member = ProjectMember(
        id=str(uuid4()),
        project_id=data.project_id,
        user_id=target.id,
        role=role,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return MemberResponse(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        role=member.role,
        email=target.email,
        display_name=target.display_name,
        created_at=member.created_at,
    )


@router.get("/comments", response_model=list[CommentResponse])
async def list_comments(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Annotated[str, Query()],
    entity_type: Annotated[str | None, Query()] = None,
    entity_id: Annotated[str | None, Query()] = None,
):
    query = select(Comment, User).join(User, User.id == Comment.user_id).where(
        Comment.project_id == project_id,
    )
    if entity_type:
        query = query.where(Comment.entity_type == entity_type)
    if entity_id:
        query = query.where(Comment.entity_id == entity_id)
    query = query.order_by(Comment.created_at.desc())
    result = await db.execute(query)
    return [
        CommentResponse(
            id=comment.id,
            project_id=comment.project_id,
            user_id=comment.user_id,
            author_name=user.display_name,
            entity_type=comment.entity_type,
            entity_id=comment.entity_id,
            body=comment.body,
            status=comment.status,
            created_at=comment.created_at,
        )
        for comment, user in result.all()
    ]


@router.post("/comments", response_model=CommentResponse, status_code=201)
async def create_comment(
    data: CommentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    await require_project_role(db, data.project_id, user.id, "viewer")
    comment = Comment(
        id=str(uuid4()),
        project_id=data.project_id,
        user_id=user.id,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        body=data.body,
        status="open",
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return CommentResponse(
        id=comment.id,
        project_id=comment.project_id,
        user_id=comment.user_id,
        author_name=user.display_name,
        entity_type=comment.entity_type,
        entity_id=comment.entity_id,
        body=comment.body,
        status=comment.status,
        created_at=comment.created_at,
    )


@router.get("/reviews", response_model=list[ReviewProposalResponse])
async def list_reviews(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Annotated[str, Query()],
    status: Annotated[str | None, Query()] = None,
):
    query = select(ReviewProposal).where(ReviewProposal.project_id == project_id)
    if status:
        query = query.where(ReviewProposal.status == status)
    query = query.order_by(ReviewProposal.created_at.desc())
    result = await db.execute(query)
    proposals = list(result.scalars().all())
    return [await _proposal_response(db, p) for p in proposals]


@router.post("/reviews", response_model=ReviewProposalResponse, status_code=201)
async def create_review(
    data: ReviewProposalCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    await require_project_role(db, data.project_id, user.id, "editor")
    proposal = ReviewProposal(
        id=str(uuid4()),
        project_id=data.project_id,
        created_by_id=user.id,
        assignee_id=data.assignee_id,
        title=data.title,
        description=data.description,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        status="pending",
    )
    db.add(proposal)
    await db.flush()
    if proposal.assignee_id:
        await _notify_assignee(db, proposal, actor=user)
    await db.commit()
    await db.refresh(proposal)
    return await _proposal_response(db, proposal)


@router.post("/reviews/{proposal_id}/simulate", response_model=PeerReviewSimulation)
async def simulate_review(
    proposal_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Generate simulated peer-review feedback for a proposal."""
    from app.api.research import get_llm_router
    from app.services.peer_review_service import PeerReviewService

    proposal = await db.get(ReviewProposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Review proposal not found")
    await require_project_role(db, proposal.project_id, user.id, "editor")

    service = PeerReviewService(db, get_llm_router())
    try:
        feedback = await service.simulate_review(proposal_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PeerReviewSimulation(**feedback)


@router.patch("/reviews/{proposal_id}", response_model=ReviewProposalResponse)
async def update_review(
    proposal_id: str,
    data: ReviewProposalUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    proposal = await db.get(ReviewProposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Review proposal not found")
    await require_project_role(db, proposal.project_id, user.id, "editor")

    if data.status is not None:
        proposal.status = data.status
    if data.assignee_id is not None:
        proposal.assignee_id = data.assignee_id
        await _notify_assignee(db, proposal, actor=user)

    await db.commit()
    await db.refresh(proposal)
    return await _proposal_response(db, proposal)


@router.get("/activity", response_model=list[ActivityItem])
async def project_activity(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Annotated[str, Query()],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    service = ActivityFeedService(db)
    items = await service.get_feed(project_id, limit=limit)
    return [ActivityItem(**item) for item in items]


@router.get("/notifications", response_model=list[ReviewNotification])
async def review_notifications(
    project_id: Annotated[str, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Pending review assignments for the current user."""
    await require_project_role(db, project_id, user.id, "viewer")
    result = await db.execute(
        select(ReviewProposal)
        .where(
            ReviewProposal.project_id == project_id,
            ReviewProposal.assignee_id == user.id,
            ReviewProposal.status.in_(("pending", "in_review")),
        )
        .order_by(ReviewProposal.created_at.desc()),
    )
    proposals = list(result.scalars().all())
    return [
        ReviewNotification(
            id=f"notif-{p.id}",
            proposal_id=p.id,
            project_id=p.project_id,
            title=p.title,
            status=p.status,
            assignee_id=p.assignee_id or user.id,
            created_at=p.created_at,
        )
        for p in proposals
    ]


async def _notify_assignee(
    db: AsyncSession,
    proposal: ReviewProposal,
    *,
    actor: User,
) -> None:
    if not proposal.assignee_id:
        return
    assignee = await db.get(User, proposal.assignee_id)
    audit = AuditService(db)
    await audit.log_event(
        event_type="review_assigned",
        project_id=proposal.project_id,
        actor=actor.display_name,
        action=f"Assigned review '{proposal.title}' to {assignee.display_name if assignee else proposal.assignee_id}",
        details={
            "proposal_id": proposal.id,
            "assignee_id": proposal.assignee_id,
            "entity_type": proposal.entity_type,
            "entity_id": proposal.entity_id,
        },
    )
    if assignee:
        from app.services.notification_service import NotificationService

        notifier = NotificationService()
        await notifier.send_review_assignment(
            assignee_email=assignee.email,
            assignee_name=assignee.display_name,
            proposal_title=proposal.title,
            project_id=proposal.project_id,
            proposal_id=proposal.id,
            actor_name=actor.display_name,
        )


async def _proposal_response(db: AsyncSession, proposal: ReviewProposal) -> ReviewProposalResponse:
    creator = await db.get(User, proposal.created_by_id)
    assignee = await db.get(User, proposal.assignee_id) if proposal.assignee_id else None
    return ReviewProposalResponse(
        id=proposal.id,
        project_id=proposal.project_id,
        created_by_id=proposal.created_by_id,
        created_by_name=creator.display_name if creator else "Unknown",
        assignee_id=proposal.assignee_id,
        assignee_name=assignee.display_name if assignee else None,
        title=proposal.title,
        description=proposal.description,
        entity_type=proposal.entity_type,
        entity_id=proposal.entity_id,
        status=proposal.status,
        created_at=proposal.created_at,
    )
