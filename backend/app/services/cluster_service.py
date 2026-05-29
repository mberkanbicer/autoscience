"""Cluster service for storing and managing paper clusters."""

from uuid import uuid4
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.paper import PaperCluster, ClusterLabel
from ..engine.clustering import PaperCluster as ClusteringPaperCluster


class ClusterService:
    """Service for storing and managing paper clusters."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_clusters(
        self,
        project_id: str,
        clusters: list[ClusteringPaperCluster],
    ) -> list[PaperCluster]:
        """Store clusters in the database."""
        stored_clusters = []

        for cluster in clusters:
            # Create cluster record
            cluster_record = PaperCluster(
                id=cluster.id,
                project_id=project_id,
                name=cluster.name,
                description=cluster.description,
                cluster_type=cluster.cluster_type,
                paper_ids=cluster.paper_ids,
                representative_paper_id=cluster.representative_paper_id,
            )
            self.db.add(cluster_record)

            # Add labels
            for label in cluster.labels:
                label_record = ClusterLabel(
                    id=str(uuid4()),
                    cluster_id=cluster.id,
                    label=label,
                    rationale=f"Label for {cluster.name}",
                )
                self.db.add(label_record)

            stored_clusters.append(cluster_record)

        await self.db.flush()
        return stored_clusters

    async def get_project_clusters(
        self,
        project_id: str,
        cluster_type: str | None = None,
    ) -> list[PaperCluster]:
        """Get all clusters for a project."""
        query = select(PaperCluster).where(PaperCluster.project_id == project_id)

        if cluster_type:
            query = query.where(PaperCluster.cluster_type == cluster_type)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_cluster(self, cluster_id: str) -> PaperCluster | None:
        """Get a cluster by ID."""
        result = await self.db.execute(
            select(PaperCluster).where(PaperCluster.id == cluster_id)
        )
        return result.scalar_one_or_none()

    async def get_cluster_with_labels(self, cluster_id: str) -> PaperCluster | None:
        """Get a cluster with its labels."""
        result = await self.db.execute(
            select(PaperCluster).where(PaperCluster.id == cluster_id)
        )
        cluster = result.scalar_one_or_none()

        if cluster:
            # Labels are loaded via relationship
            _ = cluster.labels

        return cluster

    async def update_cluster(
        self,
        cluster_id: str,
        name: str | None = None,
        description: str | None = None,
        paper_ids: list[str] | None = None,
    ) -> PaperCluster | None:
        """Update a cluster."""
        cluster = await self.get_cluster(cluster_id)
        if not cluster:
            return None

        if name is not None:
            cluster.name = name
        if description is not None:
            cluster.description = description
        if paper_ids is not None:
            cluster.paper_ids = paper_ids

        await self.db.flush()
        return cluster

    async def delete_cluster(self, cluster_id: str) -> bool:
        """Delete a cluster and its labels."""
        cluster = await self.get_cluster(cluster_id)
        if not cluster:
            return False

        # Delete labels first
        labels_result = await self.db.execute(
            select(ClusterLabel).where(ClusterLabel.cluster_id == cluster_id)
        )
        for label in labels_result.scalars().all():
            await self.db.delete(label)

        await self.db.delete(cluster)
        return True

    async def get_cluster_statistics(self, project_id: str) -> dict[str, Any]:
        """Get statistics about clusters in a project."""
        from sqlalchemy import func

        # Total clusters
        total_result = await self.db.execute(
            select(func.count(PaperCluster.id)).where(
                PaperCluster.project_id == project_id
            )
        )
        total = total_result.scalar() or 0

        # By type
        type_result = await self.db.execute(
            select(PaperCluster.cluster_type, func.count(PaperCluster.id))
            .where(PaperCluster.project_id == project_id)
            .group_by(PaperCluster.cluster_type)
        )
        by_type = {row[0] or "unknown": row[1] for row in type_result.all()}

        # Average papers per cluster
        avg_result = await self.db.execute(
            select(func.avg(func.array_length(PaperCluster.paper_ids, 1))).where(
                PaperCluster.project_id == project_id
            )
        )
        avg_papers = avg_result.scalar() or 0

        return {
            "total_clusters": total,
            "by_type": by_type,
            "avg_papers_per_cluster": round(avg_papers, 1),
        }

    async def search_clusters(
        self,
        project_id: str,
        search_text: str,
    ) -> list[PaperCluster]:
        """Search clusters by name or description."""
        search_pattern = f"%{search_text}%"

        result = await self.db.execute(
            select(PaperCluster).where(
                PaperCluster.project_id == project_id,
                (PaperCluster.name.ilike(search_pattern)) |
                (PaperCluster.description.ilike(search_pattern))
            )
        )
        return list(result.scalars().all())

    async def get_papers_in_cluster(self, cluster_id: str) -> list[str]:
        """Get paper IDs in a cluster."""
        cluster = await self.get_cluster(cluster_id)
        if not cluster:
            return []
        return cluster.paper_ids or []
