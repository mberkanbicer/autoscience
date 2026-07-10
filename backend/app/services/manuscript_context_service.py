"""Build manuscript generation context from persisted research run data."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.claims_pipeline import (
    format_claims_as_validation_results,
    format_claims_for_manuscript,
)
from app.engine.effect_size_extraction import (
    extract_effect_sizes,
    format_effect_sizes_as_validation_results,
)
from app.engine.manuscript_engine import ManuscriptGenerationParams
from app.models.idea import Idea
from app.models.paper import Paper, PaperAnalysis, PaperCluster
from app.models.report import AnalysisArtifact, AnalysisRun
from app.models.research_question import Hypothesis
from app.models.research_run import ResearchRun

_NUMERIC_RESULT_RE = re.compile(
    r"(?P<label>[A-Za-z][A-Za-z0-9 _-]{1,40})\s*[:=]\s*(?P<value>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
)


class ManuscriptContextService:
    """Assembles manuscript inputs from database records for a research run."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_run(self, run_id: str) -> ResearchRun | None:
        result = await self.db.execute(select(ResearchRun).where(ResearchRun.id == run_id))
        return result.scalar_one_or_none()

    async def get_experiment_for_run(self, run_id: str) -> dict[str, Any] | None:
        """Return the latest sandbox experiment persisted for a run."""
        result = await self.db.execute(
            select(AnalysisRun)
            .where(AnalysisRun.run_id == run_id)
            .order_by(AnalysisRun.created_at.desc())
            .limit(1),
        )
        analysis_run = result.scalar_one_or_none()
        if not analysis_run:
            return None

        artifacts_result = await self.db.execute(
            select(AnalysisArtifact)
            .where(AnalysisArtifact.analysis_run_id == analysis_run.id)
            .order_by(AnalysisArtifact.created_at),
        )
        artifacts = list(artifacts_result.scalars().all())
        stdout = next((a.description for a in artifacts if a.artifact_type == "stdout"), "")

        return {
            "analysis_run_id": analysis_run.id,
            "run_id": run_id,
            "hypothesis_id": analysis_run.hypothesis_id,
            "status": analysis_run.status,
            "success": analysis_run.status == "completed",
            "script": analysis_run.script,
            "stdout": stdout or "",
            "stderr": analysis_run.error_message or "",
            "error_message": analysis_run.error_message,
            "artifacts": [
                {
                    "id": artifact.id,
                    "artifact_type": artifact.artifact_type,
                    "description": artifact.description,
                    "file_path": artifact.file_path,
                }
                for artifact in artifacts
            ],
        }

    async def build_generation_params(
        self,
        run_id: str,
        experiment_result: dict | None = None,
        claims: list[dict[str, Any]] | None = None,
    ) -> ManuscriptGenerationParams:
        """Build manuscript generation parameters from run-linked records.

        Args:
            run_id: Research run to build parameters for.
            experiment_result: Optional in-memory experiment result that is
                injected alongside (or as fallback for) DB-persisted results.
            claims: Optional structured claims extracted from experiment output
                via the results-to-claims pipeline.

        """
        run = await self.get_run(run_id)
        if not run:
            raise ValueError(f"Research run not found: {run_id}")

        idea = None
        if run.idea_id:
            idea_result = await self.db.execute(select(Idea).where(Idea.id == run.idea_id))
            idea = idea_result.scalar_one_or_none()

        papers = await self._get_run_papers(run.project_id, run_id)
        hypotheses = await self._get_run_hypotheses(run.project_id)
        experiment = await self.get_experiment_for_run(run_id)

        # Prefer the persisted experiment, but use the in-memory result as fallback/enrichment
        if not experiment and experiment_result:
            experiment = {
                "analysis_run_id": None,
                "run_id": run_id,
                "hypothesis_id": None,
                "success": experiment_result.get("success", False),
                "status": "completed" if experiment_result.get("success", False) else "failed",
                "script": "",
                "stdout": experiment_result.get("stdout", ""),
                "stderr": experiment_result.get("stderr", ""),
                "error_message": experiment_result.get("error_message", ""),
                "artifacts": [],
            }

        paper_dicts = [
            {
                "id": paper.id,
                "title": paper.title,
                "authors": paper.authors or [],
                "year": paper.year,
                "venue": paper.venue,
                "doi": paper.doi,
                "url": paper.url,
                "abstract": paper.abstract,
                "references": paper.references or [],
            }
            for paper in papers
        ]

        findings = await self._build_findings(papers)
        # Append experiment findings when experiment data is available
        if experiment:
            stdout = (experiment.get("stdout") or "").strip()
            if stdout:
                findings.append(f"Experiment output: {stdout[:500]}")
            if experiment.get("error_message"):
                findings.append(f"Experiment error: {experiment['error_message']}")
            if experiment.get("success", False):
                findings.append("Validation experiment completed successfully.")

        # Append structured claims from the results-to-claims pipeline
        if claims:
            claim_findings = format_claims_for_manuscript(
                [_dict_to_claim(c) for c in claims],
            )
            findings.extend(claim_findings)

        validation_results = _build_validation_results(experiment)

        # Also append structured claims as validation results
        if claims:
            claim_validation = format_claims_as_validation_results(
                [_dict_to_claim(c) for c in claims],
            )
            validation_results.extend(claim_validation)

        # Build structured artifact references for cross-mode linking
        experiment_artifacts = _build_artifact_refs(experiment)
        structured_claims_list = claims or []
        structured_es_list = _build_effect_size_refs(experiment)

        return ManuscriptGenerationParams(
            idea_text=idea.current_text if idea else "",
            method_description=self._build_method_description(experiment),
            findings=findings,
            papers=paper_dicts,
            hypotheses=[
                {
                    "statement": hypothesis.statement,
                    "confidence": hypothesis.confidence,
                }
                for hypothesis in hypotheses
            ],
            validation_results=validation_results,
            experiment_artifacts=experiment_artifacts,
            structured_claims=structured_claims_list,
            structured_effect_sizes=structured_es_list,
        )

    async def _get_run_papers(self, project_id: str, run_id: str) -> list[Paper]:
        cluster_result = await self.db.execute(
            select(PaperCluster)
            .where(PaperCluster.project_id == project_id, PaperCluster.run_id == run_id)
            .order_by(PaperCluster.created_at.desc()),
        )
        clusters = list(cluster_result.scalars().all())

        paper_ids: list[str] = []
        for cluster in clusters:
            paper_ids.extend(cluster.paper_ids or [])
        paper_ids = list(dict.fromkeys(paper_ids))

        if paper_ids:
            papers_result = await self.db.execute(select(Paper).where(Paper.id.in_(paper_ids)))
            papers = list(papers_result.scalars().all())
            if papers:
                return papers

        papers_result = await self.db.execute(
            select(Paper)
            .where(Paper.project_id == project_id)
            .order_by(Paper.created_at.desc())
            .limit(20),
        )
        return list(papers_result.scalars().all())

    async def _get_run_hypotheses(self, project_id: str) -> list[Hypothesis]:
        result = await self.db.execute(
            select(Hypothesis)
            .where(Hypothesis.project_id == project_id)
            .order_by(Hypothesis.created_at.desc())
            .limit(10),
        )
        return list(result.scalars().all())

    async def _build_findings(self, papers: list[Paper]) -> list[str]:
        findings: list[str] = []
        for paper in papers[:12]:
            summary = f"{paper.title} ({paper.year or 'n.d.'})"
            if paper.abstract:
                summary += f": {paper.abstract[:240]}"
            findings.append(summary)

            analysis_result = await self.db.execute(
                select(PaperAnalysis).where(PaperAnalysis.paper_id == paper.id),
            )
            analysis = analysis_result.scalar_one_or_none()
            if analysis and analysis.findings:
                for item in analysis.findings[:2]:
                    findings.append(f"From {paper.title[:80]}: {item}")

        return findings

    def _build_method_description(self, experiment: dict[str, Any] | None) -> str | None:
        if not experiment:
            return None
        script = (experiment.get("script") or "").strip()
        if not script:
            return "Validation experiment executed in an isolated Python sandbox."
        return f"Sandbox experiment script:\n{script[:1500]}"

def _build_artifact_refs(
    experiment: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Build structured artifact reference list from experiment data.

    Returns a list of artifact dicts suitable for injection into
    manuscript generation params and for persistent linking.
    """
    if not experiment:
        return []

    refs: list[dict[str, Any]] = []
    seen: set[str] = set()

    artifacts = experiment.get("artifacts", [])
    for artifact in artifacts:
        atype = (artifact.get("artifact_type") or "").lower()
        desc = artifact.get("description") or ""
        fpath = artifact.get("file_path") or ""
        dedup_key = f"{atype}:{desc[:50]}"
        if dedup_key not in seen:
            seen.add(dedup_key)
            refs.append({
                "artifact_type": atype,
                "description": desc[:300],
                "file_path": fpath,
                "id": artifact.get("id"),
            })

    return refs


def _build_effect_size_refs(
    experiment: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Build structured effect size reference list from experiment stdout."""
    if not experiment:
        return []

    stdout = (experiment.get("stdout") or "").strip()
    if not stdout:
        return []

    es_result = extract_effect_sizes(stdout)
    return [
        {
            "effect_type": es.effect_type,
            "value": es.value,
            "label": es.label,
            "interpretation": es.interpretation,
            "direction": es.direction,
            "evidence": es.evidence[:200],
        }
        for es in es_result.effect_sizes
    ]


def _dict_to_claim(c: dict[str, Any]) -> Claim:
    """Convert a serialized claim dict back to a Claim dataclass for formatting."""
    from app.engine.claims_pipeline import Claim
    return Claim(
        statement=c.get("statement", ""),
        claim_type=c.get("claim_type", "finding"),
        confidence=c.get("confidence", 0.5),
        evidence=c.get("evidence", ""),
        metric=c.get("metric"),
        value=c.get("value"),
        source_hypothesis_id=c.get("source_hypothesis_id"),
        source_hypothesis_statement=c.get("source_hypothesis_statement"),
    )


def _build_validation_results(experiment: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Build validation results from experiment data (standalone helper)."""
    if not experiment:
        return []

    results: list[dict[str, Any]] = [
        {
            "metric": "execution_status",
            "result": "completed" if experiment.get("success") else "failed",
            "p_value": "N/A",
        },
    ]

    stdout = (experiment.get("stdout") or "").strip()
    if stdout:
        results.append(
            {
                "metric": "experiment_output",
                "result": stdout[:2000],
                "p_value": "N/A",
            },
        )
        for match in _NUMERIC_RESULT_RE.finditer(stdout):
            results.append(
                {
                    "metric": match.group("label").strip(),
                    "result": match.group("value"),
                    "p_value": "N/A",
                },
            )

        # Extract effect sizes from stdout and include them
        es_result = extract_effect_sizes(stdout)
        if es_result.effect_sizes:
            es_formatted = format_effect_sizes_as_validation_results(es_result.effect_sizes)
            results.extend(es_formatted)

    if experiment.get("error_message"):
        results.append(
            {
                "metric": "error",
                "result": experiment["error_message"],
                "p_value": "N/A",
            },
        )

    return results[:15]
