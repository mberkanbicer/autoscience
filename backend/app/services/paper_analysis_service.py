"""Paper analysis service for storing and managing analyses."""

from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.paper_analysis import PaperAnalysisResult
from app.models.paper import PaperAnalysis


class PaperAnalysisService:
    """Service for storing and managing paper analyses."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_analysis(
        self,
        analysis: PaperAnalysisResult,
    ) -> PaperAnalysis:
        """Store a paper analysis in the database."""
        # Check if analysis already exists
        existing = await self.get_analysis(analysis.paper_id)

        if existing:
            # Update existing analysis
            return await self._update_analysis(existing, analysis)

        # Create new analysis
        analysis_record = PaperAnalysis(
            id=str(uuid4()),
            paper_id=analysis.paper_id,
            problem=analysis.problem,
            method=analysis.method,
            dataset_sample=analysis.dataset_sample,
            metrics=analysis.metrics,
            findings=analysis.findings,
            limitations=analysis.limitations,
            future_work=analysis.future_work,
            assumptions=analysis.assumptions,
            key_claims=[
                {
                    "text": c.text,
                    "type": c.type,
                    "confidence": c.confidence,
                    "evidence": c.evidence,
                }
                for c in analysis.key_claims
            ],
            relation_to_idea=analysis.relation_to_idea,
            confidence=analysis.confidence,
        )
        self.db.add(analysis_record)
        await self.db.flush()

        return analysis_record

    async def _update_analysis(
        self,
        existing: PaperAnalysis,
        analysis: PaperAnalysisResult,
    ) -> PaperAnalysis:
        """Update an existing analysis with new data."""
        # Only update if new analysis has higher confidence
        if analysis.confidence > (existing.confidence or 0):
            existing.problem = analysis.problem or existing.problem
            existing.method = analysis.method or existing.method
            existing.dataset_sample = analysis.dataset_sample or existing.dataset_sample
            existing.metrics = analysis.metrics or existing.metrics
            existing.findings = analysis.findings or existing.findings
            existing.limitations = analysis.limitations or existing.limitations
            existing.future_work = analysis.future_work or existing.future_work
            existing.assumptions = analysis.assumptions or existing.assumptions
            existing.key_claims = [
                {
                    "text": c.text,
                    "type": c.type,
                    "confidence": c.confidence,
                    "evidence": c.evidence,
                }
                for c in analysis.key_claims
            ] or existing.key_claims
            existing.relation_to_idea = analysis.relation_to_idea or existing.relation_to_idea
            existing.confidence = analysis.confidence

        await self.db.flush()
        return existing

    async def get_analysis(self, paper_id: str) -> PaperAnalysis | None:
        """Get analysis for a paper."""
        result = await self.db.execute(
            select(PaperAnalysis).where(PaperAnalysis.paper_id == paper_id),
        )
        return result.scalar_one_or_none()

    async def get_analyses_for_project(
        self,
        project_id: str,
        min_confidence: float = 0.0,
    ) -> list[PaperAnalysis]:
        """Get all analyses for papers in a project."""
        from app.models.paper import Paper

        result = await self.db.execute(
            select(PaperAnalysis)
            .join(Paper, PaperAnalysis.paper_id == Paper.id)
            .where(Paper.project_id == project_id)
            .where(PaperAnalysis.confidence >= min_confidence)
            .order_by(PaperAnalysis.confidence.desc()),
        )
        return list(result.scalars().all())

    async def extract_findings_summary(
        self,
        analyses: list[PaperAnalysis],
    ) -> dict[str, Any]:
        """Extract a summary of findings from multiple analyses."""
        all_findings = []
        all_methods = []
        all_limitations = []

        for analysis in analyses:
            all_findings.extend(analysis.findings or [])
            if analysis.method:
                all_methods.append(analysis.method)
            all_limitations.extend(analysis.limitations or [])

        return {
            "total_papers_analyzed": len(analyses),
            "findings_count": len(all_findings),
            "unique_methods": list(set(all_methods)),
            "common_limitations": self._count_duplicates(all_limitations),
            "avg_confidence": (
                sum(a.confidence or 0 for a in analyses) / len(analyses)
                if analyses
                else 0
            ),
        }

    def _count_duplicates(self, items: list[str]) -> list[dict[str, Any]]:
        """Count duplicate items and return sorted by frequency."""
        counts: dict[str, int] = {}
        for item in items:
            counts[item] = counts.get(item, 0) + 1

        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [{"text": item, "count": count} for item, count in sorted_items[:10]]

    async def get_method_comparison(
        self,
        analyses: list[PaperAnalysis],
    ) -> list[dict[str, Any]]:
        """Compare methods across analyses."""
        methods = []
        for analysis in analyses:
            if analysis.method:
                methods.append({
                    "paper_id": analysis.paper_id,
                    "method": analysis.method,
                    "confidence": analysis.confidence,
                })
        return methods
