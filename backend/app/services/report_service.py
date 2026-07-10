"""Report and knowledge service layer."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import KnowledgeNote, ResearchReport


class ReportService:
    """Service for report operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_reports(
        self,
        project_id: str,
        report_type: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[ResearchReport]:
        """List reports for a project."""
        query = select(ResearchReport).where(ResearchReport.project_id == project_id)

        if report_type:
            query = query.where(ResearchReport.report_type == report_type)

        offset = (page - 1) * per_page
        query = query.order_by(ResearchReport.created_at.desc()).offset(offset).limit(per_page)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_report(
        self,
        project_id: str,
        title: str,
        content_markdown: str | None = None,
        content_html: str | None = None,
        report_type: str | None = None,
        run_id: str | None = None,
        idea_id: str | None = None,
    ) -> ResearchReport:
        """Create a new report."""
        report = ResearchReport(
            id=str(uuid4()),
            project_id=project_id,
            run_id=run_id,
            idea_id=idea_id,
            title=title,
            content_markdown=content_markdown,
            content_html=content_html,
            report_type=report_type,
        )
        self.db.add(report)
        await self.db.flush()
        return report

    async def get_report(self, report_id: str) -> ResearchReport | None:
        """Get a report by ID."""
        result = await self.db.execute(
            select(ResearchReport).where(ResearchReport.id == report_id),
        )
        return result.scalar_one_or_none()

    async def delete_report(self, report_id: str) -> bool:
        """Delete a report by ID. Returns True if deleted, False if not found."""
        report = await self.get_report(report_id)
        if not report:
            return False
        await self.db.delete(report)
        await self.db.flush()
        return True


class KnowledgeService:
    """Service for knowledge note operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_notes(
        self,
        project_id: str,
        note_type: str | None = None,
        run_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[KnowledgeNote]:
        """List knowledge notes for a project."""
        query = select(KnowledgeNote).where(KnowledgeNote.project_id == project_id)

        if note_type:
            query = query.where(KnowledgeNote.note_type == note_type)
        if run_id:
            query = query.where(KnowledgeNote.run_id == run_id)

        offset = (page - 1) * per_page
        query = query.order_by(KnowledgeNote.created_at.desc()).offset(offset).limit(per_page)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_notes(
        self,
        project_id: str,
        search_text: str,
        *,
        run_id: str | None = None,
        limit: int = 50,
    ) -> list[KnowledgeNote]:
        """Search wiki notes by title or content."""
        pattern = f"%{search_text}%"
        query = select(KnowledgeNote).where(
            KnowledgeNote.project_id == project_id,
            (KnowledgeNote.title.ilike(pattern)) | (KnowledgeNote.content.ilike(pattern)),
        )
        if run_id:
            query = query.where(KnowledgeNote.run_id == run_id)
        query = query.order_by(KnowledgeNote.updated_at.desc(), KnowledgeNote.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_note(
        self,
        project_id: str,
        note_type: str,
        title: str | None = None,
        content: str | None = None,
        entity_id: str | None = None,
        linked_notes: list[str] | None = None,
        run_id: str | None = None,
    ) -> KnowledgeNote:
        """Create a new knowledge note."""
        note = KnowledgeNote(
            id=str(uuid4()),
            project_id=project_id,
            run_id=run_id,
            note_type=note_type,
            entity_id=entity_id,
            title=title,
            content=content,
            linked_notes=linked_notes or [],
        )
        self.db.add(note)
        await self.db.flush()
        return note

    async def get_note(self, note_id: str) -> KnowledgeNote | None:
        """Get a knowledge note by ID."""
        result = await self.db.execute(
            select(KnowledgeNote).where(KnowledgeNote.id == note_id),
        )
        return result.scalar_one_or_none()

    async def update_note(
        self,
        note_id: str,
        title: str | None = None,
        content: str | None = None,
        linked_notes: list[str] | None = None,
    ) -> KnowledgeNote | None:
        """Update a knowledge note."""
        note = await self.get_note(note_id)
        if not note:
            return None

        if title is not None:
            note.title = title
        if content is not None:
            note.content = content
        if linked_notes is not None:
            note.linked_notes = linked_notes

        await self.db.flush()
        return note

    async def delete_note(self, note_id: str) -> bool:
        """Delete a knowledge note by ID. Returns True if deleted, False if not found."""
        note = await self.get_note(note_id)
        if not note:
            return False
        await self.db.delete(note)
        await self.db.flush()
        return True
