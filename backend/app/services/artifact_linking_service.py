"""Cross-mode artifact linking service.

Maps experiment artifacts (stdout, figures, tables, claims, effect sizes,
analysis scripts) to manuscript sections (introduction, methods, results,
discussion, abstract) so the connections are persistent and queryable.

This enables:
- Tracing: "which experiment outputs support this manuscript claim?"
- Provenance: "which sections reference this figure or statistic?"
- Revision: when an artifact changes, know which sections to regenerate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import AnalysisArtifact, AnalysisRun, ArtifactSectionLink

logger = structlog.get_logger()

# Section mapping: artifact types → likely manuscript sections
_ARTIFACT_TO_SECTION: dict[str, list[str]] = {
    "script": ["methods"],
    "stdout": ["results"],
    "figure": ["results"],
    "table": ["results"],
    "claim": ["results", "discussion"],
    "effect_size": ["results", "discussion"],
    "json": ["results", "methods"],
    "csv": ["results", "methods"],
    "error": ["discussion", "methods"],
}

# Section priority order for display
SECTION_ORDER = ["abstract", "introduction", "methods", "results", "discussion"]


@dataclass
class ArtifactLinkInfo:
    """Information about a single artifact-to-section link."""

    manuscript_id: str
    analysis_run_id: str | None = None
    analysis_artifact_id: str | None = None
    artifact_type: str = "claim"
    artifact_id: str | None = None
    section: str = "results"
    link_type: str = "reference"
    reference_text: str | None = None
    source_summary: str | None = None


@dataclass
class ArtifactLinkResult:
    """Result from building artifact links for a manuscript."""

    manuscript_id: str
    links_created: int = 0
    sections_with_links: list[str] = field(default_factory=list)
    artifact_types_linked: list[str] = field(default_factory=list)
    notes: str = ""


class ArtifactLinkingService:
    """Builds and queries cross-mode artifact-to-manuscript-section links."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_links(
        self,
        manuscript_id: str,
        experiment: dict[str, Any] | None = None,
        claims: list[dict[str, Any]] | None = None,
        effect_sizes: list[dict[str, Any]] | None = None,
    ) -> ArtifactLinkResult:
        """Analyze available artifacts and build section links for a manuscript.

        Args:
            manuscript_id: The manuscript to link artifacts to.
            experiment: Optional experiment result dict with stdout, stderr,
                artifacts, etc.
            claims: Optional structured claims from the results-to-claims pipeline.
            effect_sizes: Optional list of effect size dicts.

        Returns:
            ArtifactLinkResult with count of links created.

        """
        # Clear any existing links for this manuscript (idempotent)
        await self.db.execute(
            delete(ArtifactSectionLink).where(
                ArtifactSectionLink.manuscript_id == manuscript_id,
            ),
        )

        links: list[ArtifactLinkInfo] = []
        sections_touched: set[str] = set()
        types_touched: set[str] = set()

        # --- 1. Link experiment artifacts (figures, tables, stdout, scripts) ---
        if experiment:
            run_id = experiment.get("analysis_run_id")
            artifacts_list = experiment.get("artifacts", [])

            for artifact in artifacts_list:
                atype = (artifact.get("artifact_type") or "").lower()
                if atype == "stdout":
                    # Link stdout to Results section
                    links.append(ArtifactLinkInfo(
                        manuscript_id=manuscript_id,
                        artifact_type="stdout",
                        analysis_artifact_id=artifact.get("id"),
                        section="results",
                        link_type="evidence",
                        source_summary=artifact.get("description", "")[:300],
                    ))
                    sections_touched.add("results")
                    types_touched.add("stdout")
                elif atype in ("figure", "table"):
                    desc = artifact.get("description", "")[:200]
                    links.append(ArtifactLinkInfo(
                        manuscript_id=manuscript_id,
                        artifact_type=atype,
                        analysis_artifact_id=artifact.get("id"),
                        analysis_run_id=run_id,
                        section="results",
                        link_type=atype,
                        reference_text=desc or f"Experiment {atype}",
                        source_summary=artifact.get("file_path", ""),
                    ))
                    sections_touched.add("results")
                    types_touched.add(atype)
                elif atype == "script":
                    links.append(ArtifactLinkInfo(
                        manuscript_id=manuscript_id,
                        artifact_type="script",
                        analysis_artifact_id=artifact.get("id"),
                        analysis_run_id=run_id,
                        section="methods",
                        link_type="code",
                        source_summary=artifact.get("description", "")[:300],
                    ))
                    sections_touched.add("methods")
                    types_touched.add("script")
                elif atype in ("json", "csv"):
                    links.append(ArtifactLinkInfo(
                        manuscript_id=manuscript_id,
                        artifact_type=atype,
                        analysis_artifact_id=artifact.get("id"),
                        analysis_run_id=run_id,
                        section="results",
                        link_type="evidence",
                        source_summary=artifact.get("description", "")[:200],
                    ))
                    sections_touched.add("results")
                    types_touched.add(atype)

            # Link experiment stdout content as textual evidence
            stdout_text = (experiment.get("stdout") or "").strip()
            if stdout_text:
                stderr_text = (experiment.get("stderr") or "").strip()
                links.append(ArtifactLinkInfo(
                    manuscript_id=manuscript_id,
                    analysis_run_id=run_id,
                    artifact_type="stdout",
                    artifact_id=run_id,
                    section="results",
                    link_type="evidence",
                    source_summary=stdout_text[:500],
                ))
                sections_touched.add("results")
                types_touched.add("stdout")

                if stderr_text:
                    links.append(ArtifactLinkInfo(
                        manuscript_id=manuscript_id,
                        analysis_run_id=run_id,
                        artifact_type="stdout",
                        artifact_id=run_id,
                        section="discussion",
                        link_type="evidence",
                        source_summary=f"Error output: {stderr_text[:300]}",
                    ))
                    sections_touched.add("discussion")
                    types_touched.add("stdout")

            # Link execution success/failure
            if experiment.get("success") is not None:
                success = experiment.get("success", False)
                links.append(ArtifactLinkInfo(
                    manuscript_id=manuscript_id,
                    analysis_run_id=run_id,
                    artifact_type="claim",
                    artifact_id=run_id,
                    section="results",
                    link_type="finding",
                    source_summary=f"Experiment {'succeeded' if success else 'failed'}",
                ))
                sections_touched.add("results")
                types_touched.add("claim")

        # --- 2. Link structured claims ---
        if claims:
            for i, claim in enumerate(claims):
                ctype = (claim.get("claim_type") or "finding").lower()
                statement = claim.get("statement", "")
                section = "results"
                link_type = "finding"

                if ctype == "error":
                    section = "discussion"
                    link_type = "evidence"
                elif ctype == "statistical":
                    section = "results"
                    link_type = "statistic"
                elif ctype in ("improvement", "degradation"):
                    section = "discussion"
                    link_type = "finding"

                links.append(ArtifactLinkInfo(
                    manuscript_id=manuscript_id,
                    artifact_type="claim",
                    artifact_id=f"claim_{i}",
                    section=section,
                    link_type=link_type,
                    reference_text=statement[:200] if statement else None,
                    source_summary=claim.get("evidence", "")[:300],
                ))
                sections_touched.add(section)
                types_touched.add("claim")

        # --- 3. Link effect sizes ---
        if effect_sizes:
            for i, es in enumerate(effect_sizes):
                es_type = es.get("effect_type", "cohens_d")
                label = es.get("label", es_type)
                value = es.get("value")
                interp = es.get("interpretation", "")

                summary = f"{label} = {value:.4f}"
                if interp:
                    summary += f" ({interp.replace('_', ' ')})"

                links.append(ArtifactLinkInfo(
                    manuscript_id=manuscript_id,
                    artifact_type="effect_size",
                    artifact_id=f"effect_size_{i}",
                    section="results",
                    link_type="statistic",
                    reference_text=summary,
                    source_summary=es.get("evidence", "")[:300],
                ))
                sections_touched.add("results")
                types_touched.add("effect_size")

                # Large effect sizes also linked to discussion
                if interp in ("large", "very_large"):
                    links.append(ArtifactLinkInfo(
                        manuscript_id=manuscript_id,
                        artifact_type="effect_size",
                        artifact_id=f"effect_size_{i}",
                        section="discussion",
                        link_type="finding",
                        reference_text=f"Notable: {summary}",
                        source_summary=es.get("evidence", "")[:300],
                    ))
                    sections_touched.add("discussion")

        # --- Persist all links ---
        persisted_count = 0
        for info in links:
            link_record = ArtifactSectionLink(
                id=str(uuid4()),
                manuscript_id=info.manuscript_id,
                analysis_run_id=info.analysis_run_id,
                analysis_artifact_id=info.analysis_artifact_id,
                artifact_type=info.artifact_type,
                artifact_id=info.artifact_id,
                section=info.section,
                link_type=info.link_type,
                reference_text=info.reference_text,
                source_summary=info.source_summary,
            )
            self.db.add(link_record)
            persisted_count += 1

        await self.db.flush()

        if persisted_count:
            logger.info(
                "artifact_links_built",
                manuscript_id=manuscript_id,
                links=persisted_count,
                sections=list(sections_touched),
                types=list(types_touched),
            )

        return ArtifactLinkResult(
            manuscript_id=manuscript_id,
            links_created=persisted_count,
            sections_with_links=sorted(sections_touched, key=lambda s: SECTION_ORDER.index(s) if s in SECTION_ORDER else 99),
            artifact_types_linked=sorted(types_touched),
            notes=(
                f"Linked {persisted_count} artifact references "
                f"across {len(sections_touched)} section(s) "
                f"({', '.join(sorted(types_touched))})."
            ),
        )

    async def get_links_for_manuscript(
        self,
        manuscript_id: str,
        section: str | None = None,
        artifact_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get all artifact links for a manuscript, with optional filters.

        Args:
            manuscript_id: Manuscript to query.
            section: Optional section filter (e.g. "results", "methods").
            artifact_type: Optional artifact type filter.

        Returns:
            List of link dicts with artifact details.

        """
        query = (
            select(
                ArtifactSectionLink,
                AnalysisRun.run_id,
                AnalysisArtifact.file_path,
                AnalysisArtifact.description,
            )
            .outerjoin(
                AnalysisRun,
                ArtifactSectionLink.analysis_run_id == AnalysisRun.id,
            )
            .outerjoin(
                AnalysisArtifact,
                ArtifactSectionLink.analysis_artifact_id == AnalysisArtifact.id,
            )
            .where(ArtifactSectionLink.manuscript_id == manuscript_id)
        )

        if section:
            query = query.where(ArtifactSectionLink.section == section)
        if artifact_type:
            query = query.where(ArtifactSectionLink.artifact_type == artifact_type)

        query = query.order_by(ArtifactSectionLink.section, ArtifactSectionLink.created_at)
        result = await self.db.execute(query)
        rows = result.all()

        links: list[dict[str, Any]] = []
        for link, parent_run_id, file_path, artifact_desc in rows:
            links.append({
                "id": link.id,
                "manuscript_id": link.manuscript_id,
                "analysis_run_id": link.analysis_run_id,
                "analysis_artifact_id": link.analysis_artifact_id,
                "artifact_type": link.artifact_type,
                "artifact_id": link.artifact_id,
                "section": link.section,
                "link_type": link.link_type,
                "reference_text": link.reference_text,
                "source_summary": link.source_summary,
                "parent_run_id": parent_run_id,
                "artifact_file_path": file_path,
                "artifact_description": artifact_desc,
                "created_at": link.created_at.isoformat() if link.created_at else None,
            })

        return links

    async def get_linked_artifacts_by_section(
        self,
        manuscript_id: str,
    ) -> dict[str, list[dict[str, Any]]]:
        """Get all links grouped by section for a manuscript.

        Returns dict like:
        {
            "results": [...links...],
            "methods": [...links...],
            "discussion": [...links...],
        }
        """
        links = await self.get_links_for_manuscript(manuscript_id)
        grouped: dict[str, list[dict[str, Any]]] = {}

        for link in links:
            section = link.get("section", "other")
            grouped.setdefault(section, []).append(link)

        return grouped

    async def get_artifacts_for_section(
        self,
        manuscript_id: str,
        section: str,
    ) -> list[dict[str, Any]]:
        """Get all artifacts linked to a specific manuscript section."""
        return await self.get_links_for_manuscript(manuscript_id, section=section)
