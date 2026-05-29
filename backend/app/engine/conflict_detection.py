"""Conflict and gap detection engine for identifying scientific tensions."""

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import structlog

from ..llm.base import Message
from ..llm.router import LLMRouter

logger = structlog.get_logger()


@dataclass
class Conflict:
    """A scientific conflict between papers."""

    id: str
    conflict_type: str  # finding, method, dataset, metric, assumption, scope, theory_practice, recency, replication
    description: str
    supporting_papers: list[str] = field(default_factory=list)
    opposing_papers: list[str] = field(default_factory=list)
    research_opportunity: str = ""
    severity: float = 0.5  # 0-1
    cluster_id: str | None = None


@dataclass
class Gap:
    """A research gap or limitation."""

    id: str
    description: str
    gap_type: str  # missing_baseline, limited_validation, unexplored_condition, repeated_limitation, other
    related_papers: list[str] = field(default_factory=list)
    opportunity: str = ""
    severity: float = 0.5


@dataclass
class ConflictDetectionResult:
    """Result from conflict detection."""

    conflicts: list[Conflict] = field(default_factory=list)
    gaps: list[Gap] = field(default_factory=list)
    analysis_notes: str = ""
    total_conflicts: int = 0
    total_gaps: int = 0
    high_severity_count: int = 0


class ConflictDetectionEngine:
    """Engine for detecting conflicts and gaps in scientific literature."""

    def __init__(self, llm_router: LLMRouter):
        self.llm = llm_router

    async def detect_conflicts(
        self,
        papers: list[dict[str, Any]],
        cluster_id: str | None = None,
    ) -> ConflictDetectionResult:
        """Detect conflicts between papers."""
        if len(papers) < 2:
            return ConflictDetectionResult()

        # Detect different types of conflicts
        finding_conflicts = await self._detect_finding_conflicts(papers)
        method_conflicts = await self._detect_method_conflicts(papers)
        assumption_conflicts = await self._detect_assumption_conflicts(papers)

        # Combine all conflicts
        all_conflicts = finding_conflicts + method_conflicts + assumption_conflicts

        # Add cluster ID to all conflicts
        for conflict in all_conflicts:
            conflict.cluster_id = cluster_id

        # Detect gaps
        gaps = await self._detect_gaps(papers)

        # Calculate statistics
        high_severity = sum(1 for c in all_conflicts if c.severity >= 0.7)

        # Generate analysis notes
        notes = await self._generate_analysis_notes(all_conflicts, gaps, papers)

        return ConflictDetectionResult(
            conflicts=all_conflicts,
            gaps=gaps,
            analysis_notes=notes,
            total_conflicts=len(all_conflicts),
            total_gaps=len(gaps),
            high_severity_count=high_severity,
        )

    async def _detect_finding_conflicts(
        self,
        papers: list[dict[str, Any]],
    ) -> list[Conflict]:
        """Detect conflicts in findings between papers."""
        papers_summary = self._prepare_papers_summary(papers, include_findings=True)

        system = """You are a scientific conflict detection expert.

Detect conflicts in findings between papers.

Output a JSON object with:
- conflicts: Array of conflict objects, each with:
  - description: Clear description of the conflict (string)
  - supporting_papers: Paper IDs supporting one side (array of strings)
  - opposing_papers: Paper IDs supporting the other side (array of strings)
  - research_opportunity: How this conflict could be resolved (string)
  - severity: 0-1 float (1 = major conflict, 0 = minor difference)

Focus on genuine contradictions, not just different focuses."""

        user = f"""Papers:
{papers_summary}

Detect conflicts in findings between these papers."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        conflicts = []
        for c in result.data.get("conflicts", []):
            conflicts.append(
                Conflict(
                    id=str(uuid4()),
                    conflict_type="finding",
                    description=c.get("description", ""),
                    supporting_papers=c.get("supporting_papers", []),
                    opposing_papers=c.get("opposing_papers", []),
                    research_opportunity=c.get("research_opportunity", ""),
                    severity=c.get("severity", 0.5),
                )
            )

        return conflicts

    async def _detect_method_conflicts(
        self,
        papers: list[dict[str, Any]],
    ) -> list[Conflict]:
        """Detect conflicts in methods between papers."""
        papers_summary = self._prepare_papers_summary(papers, include_methods=True)

        system = """You are a scientific methodology analyst.

Detect conflicts or inconsistencies in methods between papers.

Output a JSON object with:
- conflicts: Array of conflict objects, each with:
  - description: Description of the methodological conflict (string)
  - supporting_papers: Paper IDs using one method (array of strings)
  - opposing_papers: Paper IDs using conflicting method (array of strings)
  - research_opportunity: How this could be addressed (string)
  - severity: 0-1 float

Focus on methods that solve the same problem differently or produce incompatible results."""

        user = f"""Papers:
{papers_summary}

Detect methodological conflicts between these papers."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        conflicts = []
        for c in result.data.get("conflicts", []):
            conflicts.append(
                Conflict(
                    id=str(uuid4()),
                    conflict_type="method",
                    description=c.get("description", ""),
                    supporting_papers=c.get("supporting_papers", []),
                    opposing_papers=c.get("opposing_papers", []),
                    research_opportunity=c.get("research_opportunity", ""),
                    severity=c.get("severity", 0.5),
                )
            )

        return conflicts

    async def _detect_assumption_conflicts(
        self,
        papers: list[dict[str, Any]],
    ) -> list[Conflict]:
        """Detect conflicts in assumptions between papers."""
        papers_summary = self._prepare_papers_summary(papers, include_assumptions=True)

        system = """You are a scientific assumption analyst.

Detect conflicts or inconsistencies in assumptions between papers.

Output a JSON object with:
- conflicts: Array of conflict objects, each with:
  - description: Description of the assumption conflict (string)
  - supporting_papers: Paper IDs making one assumption (array of strings)
  - opposing_papers: Paper IDs making conflicting assumption (array of strings)
  - research_opportunity: How this could be addressed (string)
  - severity: 0-1 float

Focus on incompatible or contradictory assumptions."""

        user = f"""Papers:
{papers_summary}

Detect assumption conflicts between these papers."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        conflicts = []
        for c in result.data.get("conflicts", []):
            conflicts.append(
                Conflict(
                    id=str(uuid4()),
                    conflict_type="assumption",
                    description=c.get("description", ""),
                    supporting_papers=c.get("supporting_papers", []),
                    opposing_papers=c.get("opposing_papers", []),
                    research_opportunity=c.get("research_opportunity", ""),
                    severity=c.get("severity", 0.5),
                )
            )

        return conflicts

    async def _detect_gaps(
        self,
        papers: list[dict[str, Any]],
    ) -> list[Gap]:
        """Detect research gaps from papers."""
        papers_summary = self._prepare_papers_summary(
            papers, include_limitations=True, include_future_work=True
        )

        system = """You are a research gap analyst.

Detect research gaps and opportunities from these papers.

Output a JSON object with:
- gaps: Array of gap objects, each with:
  - description: Description of the gap (string)
  - gap_type: "missing_baseline" | "limited_validation" | "unexplored_condition" | "repeated_limitation" | "other" (string)
  - related_papers: Paper IDs related to this gap (array of strings)
  - opportunity: Research opportunity arising from this gap (string)
  - severity: 0-1 float (1 = critical gap, 0 = minor gap)

Focus on genuine gaps that represent research opportunities."""

        user = f"""Papers:
{papers_summary}

Detect research gaps and opportunities from these papers."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        gaps = []
        for g in result.data.get("gaps", []):
            gaps.append(
                Gap(
                    id=str(uuid4()),
                    description=g.get("description", ""),
                    gap_type=g.get("gap_type", "other"),
                    related_papers=g.get("related_papers", []),
                    opportunity=g.get("opportunity", ""),
                    severity=g.get("severity", 0.5),
                )
            )

        return gaps

    def _prepare_papers_summary(
        self,
        papers: list[dict[str, Any]],
        include_findings: bool = False,
        include_methods: bool = False,
        include_assumptions: bool = False,
        include_limitations: bool = False,
        include_future_work: bool = False,
    ) -> str:
        """Prepare a summary of papers for conflict detection."""
        summaries = []
        for i, paper in enumerate(papers[:20]):  # Limit to 20 papers
            summary = f"Paper {i+1} (ID: {paper.get('id', 'unknown')}):\n"
            summary += f"Title: {paper.get('title', 'Unknown')}\n"

            if include_findings and paper.get("findings"):
                summary += f"Findings: {', '.join(paper['findings'][:3])}\n"
            if include_methods and paper.get("method"):
                summary += f"Method: {paper['method']}\n"
            if include_assumptions and paper.get("assumptions"):
                summary += f"Assumptions: {', '.join(paper['assumptions'][:3])}\n"
            if include_limitations and paper.get("limitations"):
                summary += f"Limitations: {', '.join(paper['limitations'][:3])}\n"
            if include_future_work and paper.get("future_work"):
                summary += f"Future Work: {', '.join(paper['future_work'][:3])}\n"

            summaries.append(summary)

        return "\n".join(summaries)

    async def _generate_analysis_notes(
        self,
        conflicts: list[Conflict],
        gaps: list[Gap],
        papers: list[dict[str, Any]],
    ) -> str:
        """Generate notes about conflicts and gaps."""
        if not conflicts and not gaps:
            return "No significant conflicts or gaps detected."

        conflicts_summary = "\n".join(
            [f"- [{c.conflict_type}] {c.description[:100]}..." for c in conflicts[:5]]
        )
        gaps_summary = "\n".join(
            [f"- [{g.gap_type}] {g.description[:100]}..." for g in gaps[:5]]
        )

        system = """You are a research analysis expert.

Given conflicts and gaps detected in the literature, provide brief notes on:
1. Overview of the conflict landscape
2. Most significant tensions
3. Key research opportunities
4. Recommendations for next steps

Keep it concise (2-3 paragraphs)."""

        user = f"""Detected {len(conflicts)} conflicts and {len(gaps)} gaps from {len(papers)} papers.

Conflicts:
{conflicts_summary}

Gaps:
{gaps_summary}

Provide analysis notes."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete(messages, temperature=0.3, max_tokens=500)
        return result.content
