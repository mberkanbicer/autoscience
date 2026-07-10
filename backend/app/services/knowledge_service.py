"""Knowledge base and research wiki system."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.router import LLMRouter
from app.models.report import KnowledgeNote

logger = structlog.get_logger()


@dataclass
class WikiSection:
    """A section of the research wiki."""

    id: str
    title: str
    content: str
    note_type: str
    entity_id: str | None = None
    links: list[str] = field(default_factory=list)
    last_updated: datetime | None = None


class KnowledgeBaseService:
    """Service for managing the knowledge base and wiki."""

    def __init__(self, db: AsyncSession, llm_router: LLMRouter | None = None):
        self.db = db
        self.llm = llm_router

    async def create_note(
        self,
        project_id: str,
        note_type: str,
        title: str,
        content: str,
        entity_id: str | None = None,
        linked_notes: list[str] | None = None,
        run_id: str | None = None,
    ) -> KnowledgeNote:
        """Create a knowledge note."""
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

    async def upsert_note(
        self,
        project_id: str,
        note_type: str,
        title: str,
        content: str,
        entity_id: str | None = None,
        run_id: str | None = None,
        linked_notes: list[str] | None = None,
    ) -> KnowledgeNote:
        """Create or update a note keyed by project, type, and entity."""
        if entity_id:
            result = await self.db.execute(
                select(KnowledgeNote).where(
                    KnowledgeNote.project_id == project_id,
                    KnowledgeNote.note_type == note_type,
                    KnowledgeNote.entity_id == entity_id,
                ),
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.title = title
                existing.content = content
                if run_id:
                    existing.run_id = run_id
                if linked_notes is not None:
                    existing.linked_notes = linked_notes
                await self.db.flush()
                return existing

        return await self.create_note(
            project_id=project_id,
            note_type=note_type,
            title=title,
            content=content,
            entity_id=entity_id,
            linked_notes=linked_notes,
            run_id=run_id,
        )

    async def get_note(self, note_id: str) -> KnowledgeNote | None:
        """Get a note by ID."""
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
        """Update a note."""
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

    async def get_project_notes(
        self,
        project_id: str,
        note_type: str | None = None,
    ) -> list[KnowledgeNote]:
        """Get all notes for a project."""
        query = select(KnowledgeNote).where(KnowledgeNote.project_id == project_id)

        if note_type:
            query = query.where(KnowledgeNote.note_type == note_type)

        query = query.order_by(KnowledgeNote.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_notes(
        self,
        project_id: str,
        search_text: str,
    ) -> list[KnowledgeNote]:
        """Search notes by text."""
        search_pattern = f"%{search_text}%"

        result = await self.db.execute(
            select(KnowledgeNote).where(
                KnowledgeNote.project_id == project_id,
                (KnowledgeNote.title.ilike(search_pattern)) |
                (KnowledgeNote.content.ilike(search_pattern)),
            ),
        )
        return list(result.scalars().all())

    async def delete_note(self, note_id: str) -> bool:
        """Delete a note."""
        note = await self.get_note(note_id)
        if not note:
            return False

        await self.db.delete(note)
        await self.db.flush()
        return True

    async def generate_project_summary(
        self,
        project_id: str,
    ) -> str:
        """Generate a project summary note."""
        # Get project data
        from app.models.idea import Idea
        from app.models.paper import Paper
        from app.models.project import Project
        from app.models.research_question import Hypothesis

        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id),
        )
        project = project_result.scalar_one_or_none()
        if not project:
            return "Project not found"

        # Get counts
        ideas_count = await self.db.execute(
            select(func.count(Idea.id)).where(Idea.project_id == project_id),
        )
        papers_count = await self.db.execute(
            select(func.count(Paper.id)).where(Paper.project_id == project_id),
        )
        hypotheses_count = await self.db.execute(
            select(func.count(Hypothesis.id)).where(Hypothesis.project_id == project_id),
        )

        summary = f"""# Project Summary: {project.name}

## Overview
- **Domain:** {project.domain}
- **Description:** {project.description or 'No description'}
- **Subject Scope:** {', '.join(project.subject_scope or [])}

## Statistics
- Ideas: {ideas_count.scalar() or 0}
- Papers: {papers_count.scalar() or 0}
- Hypotheses: {hypotheses_count.scalar() or 0}

## Settings
- Idle Research: {'Enabled' if project.idle_research_enabled else 'Disabled'}
- Idle Trigger: {project.idle_trigger_minutes} minutes
- Default Flexibility: {project.default_flexibility}

---
*Auto-generated by Autoscience Knowledge Base*
"""

        # Store as note
        await self.create_note(
            project_id=project_id,
            note_type="project",
            title=f"Project Summary: {project.name}",
            content=summary,
            entity_id=project_id,
        )

        return summary

    async def generate_paper_note(
        self,
        paper_id: str,
        paper_data: dict[str, Any],
    ) -> str:
        """Generate a note for a paper."""
        note_content = f"""# Paper: {paper_data.get('title', 'Unknown')}

## Metadata
- **Authors:** {', '.join(paper_data.get('authors', [])[:5])}
- **Year:** {paper_data.get('year', 'Unknown')}
- **Venue:** {paper_data.get('venue', 'Unknown')}
- **Citations:** {paper_data.get('citation_count', 'Unknown')}
- **DOI:** {paper_data.get('doi', 'N/A')}

## Abstract
{paper_data.get('abstract', 'No abstract available')}

## Analysis
- **Problem:** {paper_data.get('problem', 'N/A')}
- **Method:** {paper_data.get('method', 'N/A')}
- **Key Findings:** {', '.join(paper_data.get('findings', [])[:3])}
- **Limitations:** {', '.join(paper_data.get('limitations', [])[:3])}

---
*Auto-generated by Autoscience Knowledge Base*
"""

        return note_content

    async def generate_cluster_note(
        self,
        cluster_data: dict[str, Any],
    ) -> str:
        """Generate a note for a cluster."""
        note_content = f"""# Cluster: {cluster_data.get('name', 'Unknown')}

## Overview
- **Type:** {cluster_data.get('cluster_type', 'Unknown')}
- **Description:** {cluster_data.get('description', 'No description')}
- **Paper Count:** {cluster_data.get('paper_count', 0)}

## Labels
{', '.join(cluster_data.get('labels', []))}

## Representative Paper
{cluster_data.get('representative_paper_title', 'N/A')}

---
*Auto-generated by Autoscience Knowledge Base*
"""

        return note_content

    async def generate_conflict_note(
        self,
        conflict_data: dict[str, Any],
    ) -> str:
        """Generate a note for a conflict."""
        note_content = f"""# Conflict: {conflict_data.get('conflict_type', 'Unknown')}

## Description
{conflict_data.get('description', 'No description')}

## Severity
{conflict_data.get('severity', 'Unknown')}

## Supporting Evidence
{chr(10).join('- ' + p for p in conflict_data.get('supporting_papers', []))}

## Opposing Evidence
{chr(10).join('- ' + p for p in conflict_data.get('opposing_papers', []))}

## Research Opportunity
{conflict_data.get('research_opportunity', 'N/A')}

---
*Auto-generated by Autoscience Knowledge Base*
"""

        return note_content

    async def generate_hypothesis_note(
        self,
        hypothesis_data: dict[str, Any],
    ) -> str:
        """Generate a note for a hypothesis."""
        note_content = f"""# Hypothesis

## Statement
{hypothesis_data.get('statement', 'No statement')}

## Variables
- **Independent:** {hypothesis_data.get('independent_variable', 'N/A')}
- **Dependent:** {hypothesis_data.get('dependent_variable', 'N/A')}

## Context
{hypothesis_data.get('context', 'N/A')}

## Expected Direction
{hypothesis_data.get('expected_direction', 'N/A')}

## Baseline
{hypothesis_data.get('baseline', 'N/A')}

## Metric
{hypothesis_data.get('metric', 'N/A')}

## Failure Condition
{hypothesis_data.get('failure_condition', 'N/A')}

## Confidence
{hypothesis_data.get('confidence', 'N/A')}

---
*Auto-generated by Autoscience Knowledge Base*
"""

        return note_content

    async def generate_skill_note(
        self,
        skill_data: dict[str, Any],
    ) -> str:
        """Generate a note for a skill."""
        note_content = f"""# Skill: {skill_data.get('name', 'Unknown')}

## Overview
- **Type:** {skill_data.get('skill_type', 'Unknown')}
- **Status:** {skill_data.get('status', 'Unknown')}
- **Version:** {skill_data.get('version', 'Unknown')}

## Purpose
{skill_data.get('purpose', 'No purpose defined')}

## Trigger Conditions
{chr(10).join('- ' + c for c in skill_data.get('trigger_conditions', []))}

## Procedure
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(skill_data.get('procedure', [])))}

## Performance
- Times Used: {skill_data.get('times_used', 0)}
- Successful Uses: {skill_data.get('successful_uses', 0)}

---
*Auto-generated by Autoscience Knowledge Base*
"""

        return note_content

    async def export_wiki_markdown(
        self,
        project_id: str,
    ) -> str:
        """Export the entire wiki as Markdown."""
        notes = await self.get_project_notes(project_id)

        # Group notes by type
        grouped: dict[str, list[KnowledgeNote]] = {}
        for note in notes:
            note_type = note.note_type or "other"
            if note_type not in grouped:
                grouped[note_type] = []
            grouped[note_type].append(note)

        # Build markdown
        sections = []
        for note_type, type_notes in grouped.items():
            sections.append(f"\n# {note_type.replace('_', ' ').title()}\n")
            for note in type_notes:
                sections.append(f"\n## {note.title}\n")
                sections.append(note.content or "")
                sections.append("")

        return "\n".join(sections)

    async def get_wiki_stats(
        self,
        project_id: str,
    ) -> dict[str, Any]:
        """Get wiki statistics."""
        notes = await self.get_project_notes(project_id)

        by_type: dict[str, int] = {}
        for note in notes:
            note_type = note.note_type or "other"
            by_type[note_type] = by_type.get(note_type, 0) + 1

        return {
            "total_notes": len(notes),
            "by_type": by_type,
        }
