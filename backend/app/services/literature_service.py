"""Literature retrieval service for storing and managing papers."""

from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.base import RawPaper
from app.models.paper import Paper, PaperSource


class LiteratureService:
    """Service for storing and managing retrieved papers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_papers(
        self,
        project_id: str,
        papers: list[RawPaper],
    ) -> list[Paper]:
        """Store retrieved papers in the database."""
        stored_papers = []

        for raw_paper in papers:
            # Check if paper already exists by DOI or title
            existing = await self._find_existing_paper(
                project_id, raw_paper.doi, raw_paper.title,
            )

            if existing:
                # Update with new metadata
                await self._update_paper_metadata(existing, raw_paper)
                stored_papers.append(existing)
            else:
                # Create new paper
                paper = await self._create_paper(project_id, raw_paper)
                stored_papers.append(paper)

        await self.db.flush()
        return stored_papers

    async def _find_existing_paper(
        self,
        project_id: str,
        doi: str | None,
        title: str,
    ) -> Paper | None:
        """Find an existing paper by DOI or title."""
        # Try DOI first
        if doi:
            result = await self.db.execute(
                select(Paper).where(
                    Paper.project_id == project_id,
                    Paper.doi == doi,
                ),
            )
            paper = result.scalar_one_or_none()
            if paper:
                return paper

        # Try title (exact match)
        result = await self.db.execute(
            select(Paper).where(
                Paper.project_id == project_id,
                Paper.title == title,
            ),
        )
        return result.scalar_one_or_none()

    async def _create_paper(
        self,
        project_id: str,
        raw_paper: RawPaper,
    ) -> Paper:
        """Create a new paper from raw data."""
        paper = Paper(
            id=str(uuid4()),
            project_id=project_id,
            title=raw_paper.title,
            authors=raw_paper.authors,
            year=raw_paper.year,
            doi=raw_paper.doi,
            abstract=raw_paper.abstract,
            venue=raw_paper.venue,
            url=raw_paper.url,
            citation_count=raw_paper.citation_count,
            paper_type=raw_paper.paper_type,
            source_connector=raw_paper.source,
            source_id=raw_paper.source_id,
        )
        self.db.add(paper)

        # Create source record
        source = PaperSource(
            id=str(uuid4()),
            paper_id=paper.id,
            connector=raw_paper.source,
            external_id=raw_paper.source_id,
            raw_metadata=raw_paper.raw_metadata,
        )
        self.db.add(source)

        return paper

    async def _update_paper_metadata(
        self,
        paper: Paper,
        raw_paper: RawPaper,
    ) -> None:
        """Update paper with additional metadata from raw data."""
        # Only update if we have new information
        if not paper.abstract and raw_paper.abstract:
            paper.abstract = raw_paper.abstract
        if not paper.citation_count and raw_paper.citation_count:
            paper.citation_count = raw_paper.citation_count
        if not paper.venue and raw_paper.venue:
            paper.venue = raw_paper.venue
        if not paper.url and raw_paper.url:
            paper.url = raw_paper.url

        # Merge authors if needed
        if raw_paper.authors:
            existing_authors = set(paper.authors or [])
            for author in raw_paper.authors:
                if author not in existing_authors:
                    if paper.authors is None:
                        paper.authors = []
                    paper.authors.append(author)
                    existing_authors.add(author)

        # Add source record
        source = PaperSource(
            id=str(uuid4()),
            paper_id=paper.id,
            connector=raw_paper.source,
            external_id=raw_paper.source_id,
            raw_metadata=raw_paper.raw_metadata,
        )
        self.db.add(source)

    async def get_project_papers(
        self,
        project_id: str,
        paper_type: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        limit: int = 100,
    ) -> list[Paper]:
        """Get papers for a project with optional filters."""
        query = select(Paper).where(Paper.project_id == project_id)

        if paper_type:
            query = query.where(Paper.paper_type == paper_type)
        if year_from:
            query = query.where(Paper.year >= year_from)
        if year_to:
            query = query.where(Paper.year <= year_to)

        query = query.order_by(Paper.citation_count.desc().nullslast()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_paper_with_sources(self, paper_id: str) -> Paper | None:
        """Get a paper with all its source records."""
        result = await self.db.execute(
            select(Paper).where(Paper.id == paper_id),
        )
        return result.scalar_one_or_none()

    async def search_papers(
        self,
        project_id: str,
        search_text: str,
        limit: int = 20,
    ) -> list[Paper]:
        """Search papers by title or abstract."""
        search_pattern = f"%{search_text}%"

        result = await self.db.execute(
            select(Paper).where(
                Paper.project_id == project_id,
                (Paper.title.ilike(search_pattern)) |
                (Paper.abstract.ilike(search_pattern)),
            ).limit(limit),
        )
        return list(result.scalars().all())

    async def get_paper_statistics(self, project_id: str) -> dict[str, Any]:
        """Get statistics about papers in a project."""
        from sqlalchemy import func

        # Total count
        total_result = await self.db.execute(
            select(func.count(Paper.id)).where(Paper.project_id == project_id),
        )
        total = total_result.scalar() or 0

        # By type
        type_result = await self.db.execute(
            select(Paper.paper_type, func.count(Paper.id))
            .where(Paper.project_id == project_id)
            .group_by(Paper.paper_type),
        )
        by_type = {row[0] or "unknown": row[1] for row in type_result.all()}

        # By year range
        year_result = await self.db.execute(
            select(
                func.min(Paper.year).label("earliest"),
                func.max(Paper.year).label("latest"),
                func.avg(Paper.citation_count).label("avg_citations"),
            ).where(Paper.project_id == project_id),
        )
        year_stats = year_result.one()

        return {
            "total_papers": total,
            "by_type": by_type,
            "earliest_year": year_stats.earliest,
            "latest_year": year_stats.latest,
            "avg_citations": round(year_stats.avg_citations or 0, 1),
        }
