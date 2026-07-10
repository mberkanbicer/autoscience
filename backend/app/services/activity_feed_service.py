"""Unified project activity feed."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.collaboration import Comment, ReviewProposal, User


class ActivityFeedService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_feed(self, project_id: str, *, limit: int = 50) -> list[dict]:
        items: list[dict] = []

        audit_result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.project_id == project_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit),
        )
        for log in audit_result.scalars().all():
            items.append({
                "id": log.id,
                "type": "audit",
                "actor": log.actor or "system",
                "summary": log.action or log.event_type,
                "created_at": log.created_at,
                "details": {"event_type": log.event_type, "run_id": log.run_id},
            })

        comment_result = await self.db.execute(
            select(Comment, User)
            .join(User, User.id == Comment.user_id)
            .where(Comment.project_id == project_id)
            .order_by(Comment.created_at.desc())
            .limit(limit),
        )
        for comment, user in comment_result.all():
            items.append({
                "id": comment.id,
                "type": "comment",
                "actor": user.display_name,
                "summary": f"Comment on {comment.entity_type}: {comment.body[:120]}",
                "created_at": comment.created_at,
                "details": {
                    "entity_type": comment.entity_type,
                    "entity_id": comment.entity_id,
                },
            })

        review_result = await self.db.execute(
            select(ReviewProposal, User)
            .join(User, User.id == ReviewProposal.created_by_id)
            .where(ReviewProposal.project_id == project_id)
            .order_by(ReviewProposal.created_at.desc())
            .limit(limit),
        )
        for proposal, user in review_result.all():
            items.append({
                "id": proposal.id,
                "type": "review",
                "actor": user.display_name,
                "summary": f"Review proposal: {proposal.title} ({proposal.status})",
                "created_at": proposal.created_at,
                "details": {
                    "entity_type": proposal.entity_type,
                    "entity_id": proposal.entity_id,
                    "status": proposal.status,
                    "assignee_id": proposal.assignee_id,
                },
            })

        assign_result = await self.db.execute(
            select(ReviewProposal, User)
            .join(User, User.id == ReviewProposal.created_by_id)
            .where(
                ReviewProposal.project_id == project_id,
                ReviewProposal.assignee_id.isnot(None),
            )
            .order_by(ReviewProposal.created_at.desc())
            .limit(limit),
        )
        for proposal, user in assign_result.all():
            assignee = await self.db.get(User, proposal.assignee_id)
            items.append({
                "id": f"assign-{proposal.id}",
                "type": "review_assigned",
                "actor": user.display_name,
                "summary": (
                    f"Assigned review '{proposal.title}' to "
                    f"{assignee.display_name if assignee else 'assignee'}"
                ),
                "created_at": proposal.created_at,
                "details": {
                    "proposal_id": proposal.id,
                    "assignee_id": proposal.assignee_id,
                    "status": proposal.status,
                },
            })

        items.sort(key=lambda x: x["created_at"], reverse=True)
        return items[:limit]
