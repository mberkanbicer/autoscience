"""Report generation system for research outputs."""

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import ResearchReport
from app.schemas.research_state import ResearchState

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

    def __init__(self, db: AsyncSession, llm_router=None):
        self.db = db
        self.llm = llm_router

    async def generate_report(
        self,
        state: ResearchState,
        config: ReportConfig | None = None,
    ) -> str:
        """Generate a complete research report."""
        config = config or ReportConfig()

        sections = []

        # Executive Summary - use LLM if available
        if config.include_executive_summary:
            sections.append(await self._generate_executive_summary(state))

        # Original Idea
        sections.append(self._generate_idea_section(state))

        # Literature Review - use LLM if available
        sections.append(await self._generate_literature_section(state))

        # Conflicts and Gaps - use LLM if available
        sections.append(await self._generate_conflicts_section(state))

        # Research Questions
        sections.append(self._generate_questions_section(state))

        # Hypotheses - use LLM if available
        sections.append(await self._generate_hypotheses_section(state))

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

    async def _generate_executive_summary(self, state: ResearchState) -> str:
        """Generate executive summary with LLM synthesis."""
        if self.llm and self.llm.has_provider():
            try:
                papers_summary = "\n".join(
                    f"- {p.title} ({p.year}) - {', '.join(p.authors[:2]) if p.authors else 'Unknown'}"
                    for p in state.papers[:15]
                )
                conflicts_summary = "\n".join(
                    f"- {c.conflict_type}: {c.description[:200]}"
                    for c in state.conflicts[:5]
                )
                questions_summary = "\n".join(
                    f"- {q.question}"
                    for q in state.questions[:5]
                )
                hypotheses_summary = "\n".join(
                    f"- {h.statement} (confidence: {h.confidence or 0:.2f})"
                    for h in state.hypotheses[:5]
                )
                prompt = f"""You are a scientific research analyst. Write an executive summary for this research run.

Research Idea: {state.current_idea}

Papers Analyzed ({len(state.papers)} total):
{papers_summary}

Conflicts Found ({len(state.conflicts)}):
{conflicts_summary or 'None detected.'}

Research Questions ({len(state.questions)}):
{questions_summary or 'None generated.'}

Hypotheses ({len(state.hypotheses)}):
{hypotheses_summary or 'None formed.'}

Write a concise executive summary (3-5 paragraphs) covering:
1. What was researched and why
2. Key findings from the literature
3. Main conflicts or gaps identified
4. The most promising hypotheses
5. Recommended next steps"""
                response = await self.llm.generate(prompt, max_tokens=1000)
                return f"# Executive Summary\n\n{response.strip()}\n\n## Key Metrics\n\n- Papers Analyzed: {len(state.papers)}\n- Clusters: {len(state.clusters)}\n- Conflicts: {len(state.conflicts)}\n- Questions: {len(state.questions)}\n- Hypotheses: {len(state.hypotheses)}"
            except (ValueError, RuntimeError) as e:
                logger.warning("llm_summary_failed", error=str(e))
            except Exception as e:
                logger.warning("llm_summary_unexpected", error=str(e))
        # Fallback: structured summary
        return f"""# Executive Summary

## Key Metrics

- Papers Analyzed: {len(state.papers)}
- Clusters: {len(state.clusters)}
- Conflicts: {len(state.conflicts)}
- Questions: {len(state.questions)}
- Hypotheses: {len(state.hypotheses)}

## Research Idea

{state.current_idea[:500]}{'...' if len(state.current_idea) > 500 else ''}

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

    async def _generate_literature_section(self, state: ResearchState) -> str:
        """Generate literature review section with LLM synthesis."""
        papers_list = "\n".join([
            f"- **{p.title}** ({p.year}) - {', '.join(p.authors[:2]) if p.authors else 'Unknown'}"
            for p in state.papers[:25]
        ])
        clusters_list = "\n".join([f"- {c.name}: {c.description}" for c in state.clusters])

        if self.llm and self.llm.has_provider() and state.papers:
            try:
                prompt = f"""You are a literature review analyst. Synthesize findings from these papers.

Research Topic: {state.current_idea}

Papers Found ({len(state.papers)} total, showing first 25):
{papers_list}

Clusters:
{clusters_list or 'No clustering available.'}

Write a literature review (2-4 paragraphs) covering:
1. Main themes and trends
2. Key methodologies
3. Notable findings
4. Gaps or under-explored areas"""
                response = await self.llm.generate(prompt, max_tokens=800)
                return f"# Literature Review\n\n{response.strip()}\n\n## Papers ({len(state.papers)} total)\n\n{papers_list}\n\n## Clusters\n\n{clusters_list or 'No clusters identified.'}"
            except (ValueError, RuntimeError) as e:
                logger.warning("llm_literature_review_failed", error=str(e))
            except Exception as e:
                logger.warning("llm_literature_review_unexpected", error=str(e))

        return f"""# Literature Review

## Papers Analyzed ({len(state.papers)} total)

{papers_list}

## Clusters

{clusters_list or 'No clusters identified.'}"""

    async def _generate_conflicts_section(self, state: ResearchState) -> str:
        """Generate conflicts section with LLM analysis."""
        conflicts_list = "\n".join([
            f"- **{c.conflict_type.title()}** (severity {c.severity or 0.5:.2f}): {c.description}"
            for c in state.conflicts
        ])
        if self.llm and self.llm.has_provider() and state.conflicts:
            try:
                conflicts_data = "\n".join(
                    f"- {c.conflict_type}, severity {c.severity or 0.5:.2f}: {c.description[:200]}"
                    for c in state.conflicts[:10]
                )
                prompt = f"""Analyze these research conflicts for: {state.current_idea}

Conflicts:\n{conflicts_data}\n
Write a brief analysis (2 paragraphs) about what they mean and how to resolve them."""
                response = await self.llm.generate(prompt, max_tokens=500)
                return f"# Conflicts and Gaps\n\n{response.strip()}\n\n## Detected ({len(state.conflicts)})\n\n{conflicts_list or 'No conflicts detected.'}"
            except (ValueError, RuntimeError) as e:
                logger.warning("llm_conflict_analysis_failed", error=str(e))
            except Exception as e:
                logger.warning("llm_conflict_analysis_unexpected", error=str(e))
        return f"""# Conflicts and Gaps

{len(state.conflicts)} conflicts identified.

{conflicts_list or 'No conflicts detected.'}"""

    def _generate_questions_section(self, state: ResearchState) -> str:
        """Generate research questions section."""
        questions_list = "\n".join([
            f"{i+1}. {q.question}"
            for i, q in enumerate(state.questions)
        ])

        return f"""# Research Questions

## Generated Questions

{len(state.questions)} questions generated.

{questions_list or "No questions generated."}"""

    async def _generate_hypotheses_section(self, state: ResearchState) -> str:
        """Generate hypotheses section with LLM analysis."""
        hypotheses_list = "\n".join([
            f"{i+1}. **{h.statement}** (confidence: {h.confidence or 0:.2f}, status: {h.status})"
            for i, h in enumerate(state.hypotheses)
        ])
        if self.llm and self.llm.has_provider() and state.hypotheses:
            try:
                hyp_data = "\n".join(
                    f"{i+1}. {h.statement} (confidence: {h.confidence or 0:.2f})"
                    for i, h in enumerate(state.hypotheses[:10])
                )
                prompt = f"""Evaluate these research hypotheses for: {state.current_idea}

Hypotheses:\n{hyp_data}\n
Write a brief analysis about which are most promising and what evidence would validate them."""
                response = await self.llm.generate(prompt, max_tokens=500)
                return f"# Hypotheses\n\n{response.strip()}\n\n## All ({len(state.hypotheses)})\n\n{hypotheses_list or 'No hypotheses formed.'}"
            except (ValueError, RuntimeError) as e:
                logger.warning("llm_hypothesis_analysis_failed", error=str(e))
            except Exception as e:
                logger.warning("llm_hypothesis_analysis_unexpected", error=str(e))
        return f"""# Hypotheses

{len(state.hypotheses)} hypotheses formed.

{hypotheses_list or 'No hypotheses formed.'}"""

    def _generate_validation_section(self, state: ResearchState) -> str:
        """Generate validation plan section."""
        return """# Validation Plan

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
        """Generate audit log section with timeline."""
        events_list = "\n".join([
            f"- [{e.timestamp}] **{e.event_type}** (actor: {e.actor or 'system'})"
            for e in state.events[-30:]
        ])

        # Build a timeline of workflow phases
        phase_events = [e for e in state.events if e.event_type in ("phase_changed", "step_completed")]
        timeline = "\n".join([
            f"{i+1}. **{e.event_type}** at {e.timestamp}"
            for i, e in enumerate(phase_events[-15:])
        ])

        error_count = len(state.errors)
        error_summary = ""
        if state.errors:
            error_summary = f"\n\n### Errors ({error_count})\n\n" + "\n".join(
                f"- {e.get('error_type', 'unknown')}: {e.get('message', '')[:100]}"
                for e in state.errors[:10]
            )

        return f"""# Audit Log

## Research Timeline

{timeline or 'No timeline events recorded.'}

## Events ({len(state.events)} total)

{events_list or 'No events recorded.'}

## Tool Calls

{len(state.tool_calls)} tool calls made during this research run.{error_summary}"""

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
            ResearchReport.project_id == project_id,
        )

        if report_type:
            query = query.where(ResearchReport.report_type == report_type)

        query = query.order_by(ResearchReport.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_report(self, report_id: str) -> ResearchReport | None:
        """Get a report by ID."""
        result = await self.db.execute(
            select(ResearchReport).where(ResearchReport.id == report_id),
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
        html = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html)

        # Lists
        html = re.sub(r"^- (.*)$", r"<li>\1</li>", html, flags=re.MULTILINE)

        # Paragraphs
        html = re.sub(r"\n\n", "</p><p>", html)
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
