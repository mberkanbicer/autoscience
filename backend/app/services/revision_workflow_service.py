"""Revision workflow service — closes the Research→Experiment→Article feedback loop.

This service:
1. Extracts weaknesses/gaps/questions from a manuscript (and optional peer review)
2. Generates new research questions from those gaps
3. Spawns a new research run linked to the manuscript (the revision run)
4. Generates a revised manuscript from the new run's results
5. Tracks the full lineage: parent_manuscript → revision_run → child_manuscript
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.manager import ConnectorManager
from app.llm.base import Message
from app.llm.router import LLMRouter
from app.models.report import Manuscript
from app.models.research_run import ResearchRun
from app.schemas.research_run import ResearchRunCreate
from app.services.audit_service import AuditService
from app.services.idea_ledger_service import IdeaLedgerService
from app.services.manuscript_service import ManuscriptService
from app.services.orchestrator import ResearchOrchestrator
from app.services.research_run_service import ResearchRunService

logger = structlog.get_logger()


@dataclass
class RevisionWorkflowResult:
    """Result of a revision workflow execution."""

    parent_manuscript_id: str
    revision_run_id: str
    child_manuscript_id: str | None
    questions_generated: list[str]
    gaps_identified: list[str]
    summary: str


class RevisionWorkflowService:
    """Service for the Research→Experiment→Article revision cycle."""

    def __init__(
        self,
        db: AsyncSession,
        llm_router: LLMRouter,
        connector_manager: ConnectorManager | None = None,
        event_broadcaster=None,
    ):
        self.db = db
        self.llm = llm_router
        self.connectors = connector_manager
        self.event_broadcaster = event_broadcaster
        self.run_service = ResearchRunService(db)
        self.idea_ledger = IdeaLedgerService(db)
        self.audit = AuditService(db)

    async def spawn_revision_run(
        self,
        manuscript_id: str,
        review_feedback: dict[str, Any] | None = None,
        auto_generate_manuscript: bool = True,
    ) -> RevisionWorkflowResult:
        """Spawn a new research revision run from manuscript gaps.

        Args:
            manuscript_id: The manuscript to revise.
            review_feedback: Optional peer review feedback dict with
                'weaknesses', 'questions', 'summary' keys.
            auto_generate_manuscript: If True, auto-generate a revised
                manuscript once the revision run completes.

        Returns:
            RevisionWorkflowResult with lineage tracking info.

        """
        manuscript = await self.db.get(Manuscript, manuscript_id)
        if not manuscript:
            raise ValueError(f"Manuscript not found: {manuscript_id}")

        # Step 1: Extract gaps from manuscript content and review feedback
        gaps = await self._extract_gaps(manuscript, review_feedback)

        # Step 2: Generate revision research questions from gaps
        questions = await self._generate_revision_questions(manuscript, gaps)

        # Step 3: Create a revision research run
        revision_run = await self._create_revision_run(manuscript, questions)
        revision_run_id = revision_run.id

        # Step 4: Execute the revision run
        orchestrator = self._build_orchestrator()
        await orchestrator.run_research(
            project_id=manuscript.project_id,
            idea_text=f"Revision: {manuscript.title[:200]}",
            run_type="user_directed",
            existing_run_id=revision_run_id,
        )

        # Step 5: Generate revised manuscript if requested
        child_manuscript_id: str | None = None
        if auto_generate_manuscript and self.llm and self.llm.has_provider():
            try:
                ms = ManuscriptService(self.db, self.llm)
                result = await ms.generate_for_run(revision_run_id)
                child_manuscript_id = result.id

                # Link the parent-child relationship
                result.parent_manuscript_id = manuscript_id
                result.revision_run_id = revision_run_id
                await self.db.flush()
            except (ValueError, RuntimeError, SQLAlchemyError) as exc:
                logger.warning("revision_manuscript_generation_content_error", error=str(exc))
            except Exception as exc:
                logger.warning("revision_manuscript_generation_failed", error=str(exc))

        # Link manuscript to the revision run
        manuscript.revision_run_id = revision_run_id
        await self.db.flush()

        await self.audit.log_event(
            event_type="revision_workflow_completed",
            project_id=manuscript.project_id,
            details={
                "parent_manuscript_id": manuscript_id,
                "revision_run_id": revision_run_id,
                "child_manuscript_id": child_manuscript_id,
                "gaps_count": len(gaps),
                "questions_count": len(questions),
            },
        )

        logger.info(
            "revision_workflow_completed",
            manuscript_id=manuscript_id,
            run_id=revision_run_id,
            child_manuscript_id=child_manuscript_id,
            gaps=len(gaps),
            questions=len(questions),
        )

        return RevisionWorkflowResult(
            parent_manuscript_id=manuscript_id,
            revision_run_id=revision_run_id,
            child_manuscript_id=child_manuscript_id,
            questions_generated=questions,
            gaps_identified=[g.description for g in gaps],
            summary=(
                f"Revision run {revision_run_id[:8]} spawned from manuscript "
                f"{manuscript_id[:8]}. Identified {len(gaps)} gaps, "
                f"generated {len(questions)} revision questions."
            ),
        )

    async def _extract_gaps(
        self,
        manuscript: Manuscript,
        review_feedback: dict[str, Any] | None,
    ) -> list[ManuscriptGap]:
        """Extract gaps/weaknesses from manuscript content and review feedback."""
        gaps: list[ManuscriptGap] = []

        # Gaps from peer review feedback
        if review_feedback:
            for w in review_feedback.get("weaknesses", []):
                gaps.append(ManuscriptGap(
                    description=str(w),
                    source="peer_review",
                    severity=_infer_severity(str(w)),
                ))
            for q in review_feedback.get("questions", []):
                gaps.append(ManuscriptGap(
                    description=f"Unresolved reviewer question: {q}",
                    source="peer_review",
                    severity=0.6,
                ))

        # Gaps from manuscript discussion section (limitations)
        if manuscript.content_latex:
            latex = manuscript.content_latex.lower()
            # Look for discussion / limitations section markers
            for section_marker in ["\\section{discussion}", "\\section{conclusion}", "limitation"]:
                if section_marker in latex:
                    idx = latex.index(section_marker)
                    snippet = latex[idx: idx + 2000]
                    # Use LLM to extract specific limitations
                    if self.llm and self.llm.has_provider():
                        try:
                            llm_gaps = await self._llm_extract_gaps(snippet)
                            gaps.extend(llm_gaps)
                        except (ValueError, RuntimeError) as exc:
                            logger.warning("revision_llm_gap_extraction_error", error=str(exc))
                        except Exception as exc:
                            logger.warning("revision_llm_gap_extraction_failed", error=str(exc))
                    break

            # Also extract generic gaps via keyword heuristics
            gap_keywords = [
                ("further research", "Further research needed", 0.5),
                ("future work", "Future work required", 0.5),
                ("open question", "Open question remains", 0.6),
                ("unexplored", "Unexplored aspect", 0.6),
                ("not addressed", "Not addressed in this study", 0.7),
                ("limitation", "Study limitation", 0.8),
                ("unclear", "Unclear finding", 0.7),
                ("beyond the scope", "Beyond scope of current study", 0.5),
            ]
            for keyword, desc, severity in gap_keywords:
                if keyword in latex and not any(keyword in g.description.lower() for g in gaps):
                    gaps.append(ManuscriptGap(
                        description=desc,
                        source="manuscript_text",
                        severity=severity,
                    ))

        if not gaps:
            gaps.append(ManuscriptGap(
                description="General revision: strengthen methods and broaden evidence base",
                source="default",
                severity=0.5,
            ))

        return gaps

    async def _llm_extract_gaps(self, snippet: str) -> list[ManuscriptGap]:
        """Use LLM to extract specific limitations from a manuscript section."""
        system = """You are a manuscript revision analyst. Given a discussion/conclusion section,
identify specific limitations or gaps that warrant further research.

Output a JSON object with key "gaps" containing an array of:
- description: Clear description of the gap (string)
- severity: 0-1 score indicating how critical this gap is (float)"""

        user = f"Identify research gaps from this manuscript section:\n\n{snippet[:3000]}"

        messages = [Message(role="system", content=system), Message(role="user", content=user)]
        result = await self.llm.complete_structured(messages, schema={})
        raw_gaps = result.data.get("gaps", [])

        return [
            ManuscriptGap(
                description=str(g.get("description", "")),
                source="llm_extraction",
                severity=float(g.get("severity", 0.5)),
            )
            for g in raw_gaps if g.get("description")
        ]

    async def _generate_revision_questions(
        self,
        manuscript: Manuscript,
        gaps: list[ManuscriptGap],
    ) -> list[str]:
        """Generate research questions from manuscript gaps."""
        if not self.llm or not self.llm.has_provider() or not gaps:
            # Fallback: simple template questions
            return [f"Investigate: {g.description[:120]}" for g in gaps[:5]]

        gaps_text = "\n".join(
            f"- {g.description} (severity: {g.severity:.2f}, source: {g.source})"
            for g in gaps[:10]
        )

        system = """You are a research question generator. Given gaps and limitations
identified in a manuscript, generate specific, testable research questions
that would address each gap.

Output a JSON object with key "questions" containing an array of:
- question: The research question (string)"""

        user = (
            f"Manuscript: {manuscript.title}\n\n"
            f"Identified gaps:\n{gaps_text}\n\n"
            f"Generate research questions to address these gaps."
        )

        messages = [Message(role="system", content=system), Message(role="user", content=user)]
        result = await self.llm.complete_structured(messages, schema={})
        raw_questions = result.data.get("questions", [])

        return [
            str(q.get("question", ""))
            for q in raw_questions
            if q.get("question")
        ][:8]  # Limit to 8 questions

    async def _create_revision_run(
        self,
        manuscript: Manuscript,
        questions: list[str],
    ) -> ResearchRun:
        """Create a research run linked to a manuscript revision."""
        idea_text = f"Revision: {manuscript.title[:200]}"
        if questions:
            idea_text += "\n\nRevision questions:\n" + "\n".join(f"- {q}" for q in questions)

        idea = await self.idea_ledger.create_idea(
            project_id=manuscript.project_id,
            text=idea_text,
            origin="revision_workflow",
            flexibility=0.7,
        )

        run = await self.run_service.create_run(
            project_id=manuscript.project_id,
            data=ResearchRunCreate(
                idea_id=idea.id,
                run_type="user_directed",
            ),
        )

        logger.info("revision_run_created", run_id=run.id, manuscript_id=manuscript.id)
        return run

    def _build_orchestrator(self) -> ResearchOrchestrator:
        """Build an orchestrator for executing the revision run."""
        return ResearchOrchestrator(
            db=self.db,
            llm_router=self.llm,
            connector_manager=self.connectors or ConnectorManager(),
            event_broadcaster=self.event_broadcaster,
        )

    async def get_revision_history(
        self,
        manuscript_id: str,
    ) -> list[dict[str, Any]]:
        """Get the full revision lineage for a manuscript (ancestors + descendants)."""
        history = []
        visited = set()

        async def traverse(ms_id: str, direction: str, depth: int = 0):
            if depth > 10 or ms_id in visited:
                return
            visited.add(ms_id)

            ms = await self.db.get(Manuscript, ms_id)
            if not ms:
                return

            entry = {
                "manuscript_id": ms.id,
                "title": ms.title,
                "version": ms.version,
                "status": ms.status,
                "run_id": ms.run_id,
                "revision_run_id": ms.revision_run_id,
                "direction": direction,
            }
            history.append(entry)

            if direction == "ancestors" and ms.parent_manuscript_id:
                await traverse(ms.parent_manuscript_id, "ancestors", depth + 1)

        # Traverse ancestors
        await traverse(manuscript_id, "ancestors")

        # Traverse descendants (find manuscripts that have this as parent)
        descendants = await self.db.execute(
            select(Manuscript).where(Manuscript.parent_manuscript_id == manuscript_id),
        )
        for desc in descendants.scalars().all():
            entry = {
                "manuscript_id": desc.id,
                "title": desc.title,
                "version": desc.version,
                "status": desc.status,
                "run_id": desc.run_id,
                "revision_run_id": desc.revision_run_id,
                "direction": "descendants",
            }
            history.append(entry)

        return history


@dataclass
class ManuscriptGap:
    """A gap or limitation identified in a manuscript."""

    description: str
    source: str  # peer_review | manuscript_text | llm_extraction | default
    severity: float = 0.5


def _infer_severity(text: str) -> float:
    """Infer severity from weakness text."""
    high_signals = ["fatal", "critical", "invalid", "wrong", "incorrect", "fabricated"]
    med_signals = ["unclear", "weak", "insufficient", "limited", "missing", "no evidence"]
    text_lower = text.lower()
    if any(s in text_lower for s in high_signals):
        return 0.9
    if any(s in text_lower for s in med_signals):
        return 0.7
    return 0.5
