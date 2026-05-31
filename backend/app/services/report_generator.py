"""Report generation system for research outputs."""

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.report import ResearchReport
from ..schemas.research_state import ResearchState

import structlog

logger = structlog.get_logger()


@dataclass
class ReportSection:
    """A section of a research report."""

    title: str
    content: str
    order: int
    subsections: list["ReportSection"] = field(default_factory=list)


@dataclass
class ReportConfig:
    """Configuration for report generation."""

    include_executive_summary: bool = True
    include_methodology: bool = True
    include_evidence: bool = True
    include_audit_log: bool = True
    include_citations: bool = True
    format: str = "markdown"  # markdown, html, json


class ReportGenerator:
    """Generator for research reports."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_report(
        self,
        state: ResearchState,
        config: ReportConfig | None = None,
    ) -> str:
        """Generate a complete research report."""
        config = config or ReportConfig()

        sections = []

        # Executive Summary
        if config.include_executive_summary:
            sections.append(self._generate_executive_summary(state))

        # Original Idea
        sections.append(self._generate_idea_section(state))

        # Literature Review
        sections.append(self._generate_literature_section(state))

        # Conflicts and Gaps
        sections.append(self._generate_conflicts_section(state))

        # Research Questions
        sections.append(self._generate_questions_section(state))

        # Hypotheses
        sections.append(self._generate_hypotheses_section(state))

        # Validation Plan
        sections.append(self._generate_validation_section(state))

        # Scores and Classification
        sections.append(self._generate_scoring_section(state))

        # Skills
        sections.append(self._generate_skills_section(state))

        # Audit Log
        if config.include_audit_log:
            sections.append(self._generate_audit_section(state))

        # Combine sections
        report = "\n\n".join(sections)

        return report

    def _generate_executive_summary(self, state: ResearchState) -> str:
        """Generate executive summary."""
        return f"""# Executive Summary

## Research Run Overview

- **Run ID:** {state.run_id}
- **Run Type:** {state.run_type}
- **Current Phase:** {state.current_phase}
- **Status:** {state.state}

## Key Metrics

- Papers Analyzed: {len(state.papers)}
- Clusters Identified: {len(state.clusters)}
- Conflicts Detected: {len(state.conflicts)}
- Questions Generated: {len(state.questions)}
- Hypotheses Formed: {len(state.hypotheses)}

## Research Idea

{state.current_idea[:500]}{'...' if len(state.current_idea) > 500 else ''}

## Summary

This research run analyzed {len(state.papers)} papers, identified {len(state.conflicts)} conflicts, 
generated {len(state.questions)} research questions, and formed {len(state.hypotheses)} hypotheses."""

    def _generate_idea_section(self, state: ResearchState) -> str:
        """Generate idea section."""
        return f"""# Research Idea

## Original Idea

{state.original_idea}

## Current Refined Idea

{state.current_idea}

## Flexibility Level

{state.flexibility} ({'Strict' if state.flexibility < 0.3 else 'Moderate' if state.flexibility < 0.7 else 'Flexible'})

## Idea Origin

User-directed research"""

    def _generate_literature_section(self, state: ResearchState) -> str:
        """Generate literature review section."""
        papers_by_cluster = {}
        for cluster in state.clusters:
            papers_by_cluster[cluster.name] = [
                p for p in state.papers
                if p.id in (cluster.paper_ids if hasattr(cluster, 'paper_ids') else [])
            ]

        papers_list = "\n".join([
            f"- **{p.title}** ({p.year}) - {p.citation_count or 0} citations"
            for p in state.papers[:20]
        ])

        return f"""# Literature Review

## Papers Analyzed

Total papers: {len(state.papers)}

{papers_list}

## Clusters

{len(state.clusters)} clusters identified:

{chr(10).join(f'- {c.name}: {c.description}' for c in state.clusters)}

## Literature Notes

Literature retrieval completed successfully."""

    def _generate_conflicts_section(self, state: ResearchState) -> str:
        """Generate conflicts section."""
        conflicts_list = "\n".join([
            f"""### {c.conflict_type.title()} Conflict (Severity: {c.severity or 0.5:.2f})

{c.description}
"""
            for c in state.conflicts
        ])

        return f"""# Conflicts and Gaps

## Detected Conflicts

{len(state.conflicts)} conflicts identified.

{conflicts_list if conflicts_list else "No conflicts detected."}"""

    def _generate_questions_section(self, state: ResearchState) -> str:
        """Generate research questions section."""
        questions_list = "\n".join([
            f"{i+1}. {q.question}"
            for i, q in enumerate(state.questions)
        ])

        return f"""# Research Questions

## Generated Questions

{len(state.questions)} questions generated.

{questions_list if questions_list else "No questions generated."}"""

    def _generate_hypotheses_section(self, state: ResearchState) -> str:
        """Generate hypotheses section."""
        hypotheses_list = "\n".join([
            f"""### Hypothesis {i+1}

**Statement:** {h.statement}

**Independent Variable:** {h.independent_variable}

**Dependent Variable:** {h.dependent_variable}

**Failure Condition:** {h.failure_condition}

**Confidence:** {h.confidence:.2f}
"""
            for i, h in enumerate(state.hypotheses)
        ])

        return f"""# Hypotheses

## Formed Hypotheses

{len(state.hypotheses)} hypotheses formed.

{hypotheses_list if hypotheses_list else "No hypotheses formed."}"""

    def _generate_validation_section(self, state: ResearchState) -> str:
        """Generate validation plan section."""
        return f"""# Validation Plan

## Plan Overview

Validation plans have been designed for each hypothesis.

## Next Steps

1. Identify and acquire datasets
2. Implement experimental setup
3. Run validation experiments
4. Analyze results
5. Update hypothesis confidence"""

    def _generate_scoring_section(self, state: ResearchState) -> str:
        """Generate scoring section."""
        scores_list = "\n".join([
            f"- **Overall Score:** {s.overall_value:.2f} ({s.classification})"
            for s in state.scores
        ]) if state.scores else "No scores recorded."

        return f"""# Idea Scoring

## Classification

{state.current_classification or 'Not yet classified'}

## Scores

{scores_list}"""

    def _generate_skills_section(self, state: ResearchState) -> str:
        """Generate skills section."""
        skills_used = len(state.skills_used)
        skills_created = len(state.skills_created)

        return f"""# Skills

## Skill Activity

- Skills Used: {skills_used}
- Skills Created: {skills_created}

## Skill Memory

The system has learned {skills_created} new research skills from this cycle."""

    def _generate_audit_section(self, state: ResearchState) -> str:
        """Generate audit log section."""
        events_list = "\n".join([
            f"- {e.event_type}: {e.timestamp}"
            for e in state.events[-20:]  # Last 20 events
        ])

        return f"""# Audit Log

## Events

{len(state.events)} events recorded.

{events_list if events_list else "No events recorded."}

## Tool Calls

{len(state.tool_calls)} tool calls made.

## Errors

{len(state.errors)} errors encountered."""

    async def save_report(
        self,
        project_id: str,
        run_id: str | None,
        title: str,
        content: str,
        report_type: str = "cycle",
    ) -> ResearchReport:
        """Save a report to the database."""
        report = ResearchReport(
            id=str(uuid4()),
            project_id=project_id,
            run_id=run_id,
            title=title,
            content_markdown=content,
            report_type=report_type,
        )
        self.db.add(report)
        await self.db.flush()
        return report

    async def get_project_reports(
        self,
        project_id: str,
        report_type: str | None = None,
    ) -> list[ResearchReport]:
        """Get all reports for a project."""
        query = select(ResearchReport).where(
            ResearchReport.project_id == project_id
        )

        if report_type:
            query = query.where(ResearchReport.report_type == report_type)

        query = query.order_by(ResearchReport.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_report(self, report_id: str) -> ResearchReport | None:
        """Get a report by ID."""
        result = await self.db.execute(
            select(ResearchReport).where(ResearchReport.id == report_id)
        )
        return result.scalar_one_or_none()


class ReportExporter:
    """Exporter for reports in different formats."""

    @staticmethod
    def to_markdown(report: ResearchReport) -> str:
        """Export report as Markdown."""
        return report.content_markdown or ""

    @staticmethod
    def to_html(markdown_content: str) -> str:
        """Convert Markdown to HTML."""
        # Simple markdown to HTML conversion
        html = markdown_content

        # Headers
        html = html.replace("# ", "<h1>").replace("\n# ", "\n<h1>")
        html = html.replace("## ", "<h2>").replace("\n## ", "\n<h2>")
        html = html.replace("### ", "<h3>").replace("\n### ", "\n<h3>")

        # Bold
        import re
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)

        # Lists
        html = re.sub(r'^- (.*)$', r'<li>\1</li>', html, flags=re.MULTILINE)

        # Paragraphs
        html = re.sub(r'\n\n', '</p><p>', html)
        html = f"<p>{html}</p>"

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Research Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        h3 {{ color: #666; }}
        li {{ margin: 5px 0; }}
        strong {{ color: #007bff; }}
    </style>
</head>
<body>
{html}
</body>
</html>"""

    @staticmethod
    def to_json(report: ResearchReport, state: ResearchState | None = None) -> dict[str, Any]:
        """Export report as JSON."""
        result = {
            "id": report.id,
            "project_id": report.project_id,
            "run_id": report.run_id,
            "title": report.title,
            "report_type": report.report_type,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "content_markdown": report.content_markdown,
        }

        if state:
            result["state"] = {
                "run_id": state.run_id,
                "papers_count": len(state.papers),
                "clusters_count": len(state.clusters),
                "conflicts_count": len(state.conflicts),
                "questions_count": len(state.questions),
                "hypotheses_count": len(state.hypotheses),
            }

        return result

    @staticmethod
    def to_csv_table(data: list[dict[str, Any]], filename: str = "data.csv") -> str:
        """Export data as CSV."""
        if not data:
            return ""

        headers = list(data[0].keys())
        rows = [",".join(str(row.get(h, "")) for h in headers) for row in data]

        return "\n".join([",".join(headers)] + rows)
