"""Paper service layer."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.paper import Paper, PaperAnalysis, PaperCluster, ClusterConflict
from ..schemas.paper import PaperCreate, PaperUpdate


class PaperService:
    """Service for paper operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_papers(
        self,
        project_id: str,
        paper_type: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[Paper]:
        """List papers for a project."""
        query = select(Paper).where(Paper.project_id == project_id)

        if paper_type:
            query = query.where(Paper.paper_type == paper_type)
        if year_from:
            query = query.where(Paper.year >= year_from)
        if year_to:
            query = query.where(Paper.year <= year_to)

        offset = (page - 1) * per_page
        query = query.order_by(Paper.citation_count.desc().nullslast()).offset(offset).limit(per_page)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_paper(
        self,
        project_id: str,
        data: PaperCreate,
    ) -> Paper:
        """Create a new paper."""
        paper = Paper(
            id=str(uuid4()),
            project_id=project_id,
            title=data.title,
            authors=data.authors,
            year=data.year,
            doi=data.doi,
            abstract=data.abstract,
            venue=data.venue,
            url=data.url,
            citation_count=data.citation_count,
            paper_type=data.paper_type,
            source_connector=data.source_connector,
            source_id=data.source_id,
        )
        self.db.add(paper)
        await self.db.flush()
        return paper

    async def get_paper(self, paper_id: str) -> Paper | None:
        """Get a paper by ID."""
        result = await self.db.execute(select(Paper).where(Paper.id == paper_id))
        return result.scalar_one_or_none()

    async def update_paper(self, paper_id: str, data: PaperUpdate) -> Paper | None:
        """Update a paper."""
        paper = await self.get_paper(paper_id)
        if not paper:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(paper, field, value)

        await self.db.flush()
        return paper

    async def delete_paper(self, paper_id: str) -> bool:
        """Delete a paper."""
        paper = await self.get_paper(paper_id)
        if not paper:
            return False

        await self.db.delete(paper)
        return True

    async def get_paper_analysis(self, paper_id: str) -> PaperAnalysis | None:
        """Get analysis for a paper."""
        result = await self.db.execute(
            select(PaperAnalysis).where(PaperAnalysis.paper_id == paper_id)
        )
        return result.scalar_one_or_none()

    async def create_paper_analysis(
        self,
        paper_id: str,
        analysis_data: dict,
    ) -> PaperAnalysis:
        """Create or update paper analysis."""
        existing = await self.get_paper_analysis(paper_id)

        if existing:
            for field, value in analysis_data.items():
                setattr(existing, field, value)
            await self.db.flush()
            return existing

        analysis = PaperAnalysis(
            id=str(uuid4()),
            paper_id=paper_id,
            problem=analysis_data.get("problem"),
            method=analysis_data.get("method"),
            dataset_sample=analysis_data.get("dataset_sample"),
            metrics=analysis_data.get("metrics", []),
            findings=analysis_data.get("findings", []),
            limitations=analysis_data.get("limitations", []),
            future_work=analysis_data.get("future_work", []),
            assumptions=analysis_data.get("assumptions", []),
            relation_to_idea=analysis_data.get("relation_to_idea"),
            key_claims=analysis_data.get("key_claims", []),
            confidence=analysis_data.get("confidence"),
        )
        self.db.add(analysis)
        await self.db.flush()
        return analysis

    async def list_clusters(
        self,
        project_id: str,
        cluster_type: str | None = None,
    ) -> list[PaperCluster]:
        """List paper clusters for a project."""
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

    async def list_conflicts(
        self,
        project_id: str,
        conflict_type: str | None = None,
        cluster_id: str | None = None,
    ) -> list[ClusterConflict]:
        """List conflicts for a project."""
        query = select(ClusterConflict).where(ClusterConflict.project_id == project_id)

        if conflict_type:
            query = query.where(ClusterConflict.conflict_type == conflict_type)
        if cluster_id:
            query = query.where(ClusterConflict.cluster_id == cluster_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_conflict(self, conflict_id: str) -> ClusterConflict | None:
        """Get a conflict by ID."""
        result = await self.db.execute(
            select(ClusterConflict).where(ClusterConflict.id == conflict_id)
        )
        return result.scalar_one_or_none()

    async def create_conflict(
        self,
        project_id: str,
        conflict_data: dict,
    ) -> ClusterConflict:
        """Create a new conflict."""
        conflict = ClusterConflict(
            id=str(uuid4()),
            project_id=project_id,
            cluster_id=conflict_data.get("cluster_id"),
            conflict_type=conflict_data["conflict_type"],
            description=conflict_data["description"],
            supporting_papers=conflict_data.get("supporting_papers", []),
            opposing_papers=conflict_data.get("opposing_papers", []),
            research_opportunity=conflict_data.get("research_opportunity"),
            severity=conflict_data.get("severity"),
        )
        self.db.add(conflict)
        await self.db.flush()
        return conflict
