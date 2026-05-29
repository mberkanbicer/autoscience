"""Conflict service for storing and managing detected conflicts."""

from uuid import uuid4
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.paper import ClusterConflict
from ..engine.conflict_detection import Conflict, Gap, ConflictDetectionResult


class ConflictService:
    """Service for storing and managing conflicts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_conflicts(
        self,
        project_id: str,
        result: ConflictDetectionResult,
        cluster_id: str | None = None,
    ) -> list[ClusterConflict]:
        """Store detected conflicts in the database."""
        stored_conflicts = []

        for conflict in result.conflicts:
            conflict_record = ClusterConflict(
                id=conflict.id,
                project_id=project_id,
                cluster_id=cluster_id or conflict.cluster_id,
                conflict_type=conflict.conflict_type,
                description=conflict.description,
                supporting_papers=conflict.supporting_papers,
                opposing_papers=conflict.opposing_papers,
                research_opportunity=conflict.research_opportunity,
                severity=conflict.severity,
            )
            self.db.add(conflict_record)
            stored_conflicts.append(conflict_record)

        await self.db.flush()
        return stored_conflicts

    async def get_project_conflicts(
        self,
        project_id: str,
        conflict_type: str | None = None,
        min_severity: float = 0.0,
    ) -> list[ClusterConflict]:
        """Get all conflicts for a project."""
        query = select(ClusterConflict).where(
            ClusterConflict.project_id == project_id
        )

        if conflict_type:
            query = query.where(ClusterConflict.conflict_type == conflict_type)

        if min_severity > 0:
            query = query.where(ClusterConflict.severity >= min_severity)

        query = query.order_by(ClusterConflict.severity.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_conflict(self, conflict_id: str) -> ClusterConflict | None:
        """Get a conflict by ID."""
        result = await self.db.execute(
            select(ClusterConflict).where(ClusterConflict.id == conflict_id)
        )
        return result.scalar_one_or_none()

    async def get_cluster_conflicts(self, cluster_id: str) -> list[ClusterConflict]:
        """Get all conflicts for a cluster."""
        result = await self.db.execute(
            select(ClusterConflict).where(ClusterConflict.cluster_id == cluster_id)
        )
        return list(result.scalars().all())

    async def update_conflict(
        self,
        conflict_id: str,
        description: str | None = None,
        research_opportunity: str | None = None,
        severity: float | None = None,
    ) -> ClusterConflict | None:
        """Update a conflict."""
        conflict = await self.get_conflict(conflict_id)
        if not conflict:
            return None

        if description is not None:
            conflict.description = description
        if research_opportunity is not None:
            conflict.research_opportunity = research_opportunity
        if severity is not None:
            conflict.severity = severity

        await self.db.flush()
        return conflict

    async def delete_conflict(self, conflict_id: str) -> bool:
        """Delete a conflict."""
        conflict = await self.get_conflict(conflict_id)
        if not conflict:
            return False

        await self.db.delete(conflict)
        return True

    async def get_conflict_statistics(self, project_id: str) -> dict[str, Any]:
        """Get statistics about conflicts in a project."""
        from sqlalchemy import func

        # Total conflicts
        total_result = await self.db.execute(
            select(func.count(ClusterConflict.id)).where(
                ClusterConflict.project_id == project_id
            )
        )
        total = total_result.scalar() or 0

        # By type
        type_result = await self.db.execute(
            select(ClusterConflict.conflict_type, func.count(ClusterConflict.id))
            .where(ClusterConflict.project_id == project_id)
            .group_by(ClusterConflict.conflict_type)
        )
        by_type = {row[0] or "unknown": row[1] for row in type_result.all()}

        # By severity
        severity_result = await self.db.execute(
            select(
                func.avg(ClusterConflict.severity).label("avg_severity"),
                func.max(ClusterConflict.severity).label("max_severity"),
            ).where(ClusterConflict.project_id == project_id)
        )
        severity_stats = severity_result.one()

        # High severity count
        high_severity_result = await self.db.execute(
            select(func.count(ClusterConflict.id)).where(
                ClusterConflict.project_id == project_id,
                ClusterConflict.severity >= 0.7,
            )
        )
        high_severity = high_severity_result.scalar() or 0

        return {
            "total_conflicts": total,
            "by_type": by_type,
            "avg_severity": round(severity_stats.avg_severity or 0, 2),
            "max_severity": round(severity_stats.max_severity or 0, 2),
            "high_severity_count": high_severity,
        }

    async def search_conflicts(
        self,
        project_id: str,
        search_text: str,
    ) -> list[ClusterConflict]:
        """Search conflicts by description."""
        search_pattern = f"%{search_text}%"

        result = await self.db.execute(
            select(ClusterConflict).where(
                ClusterConflict.project_id == project_id,
                ClusterConflict.description.ilike(search_pattern),
            )
        )
        return list(result.scalars().all())
