"""Simulated peer-review feedback for proposals and manuscripts."""

from __future__ import annotations

import json
import re
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentInput, AgentRole, create_agent
from app.llm.router import LLMRouter
from app.models.collaboration import ReviewProposal
from app.models.idea import Idea
from app.models.paper import Paper
from app.models.report import Manuscript
from app.models.research_question import Hypothesis
from app.models.research_run import ResearchRun

logger = structlog.get_logger()


class PeerReviewService:
    def __init__(self, db: AsyncSession, llm_router: LLMRouter):
        self.db = db
        self.llm = llm_router

    async def simulate_review(self, proposal_id: str) -> dict[str, Any]:
        proposal = await self.db.get(ReviewProposal, proposal_id)
        if not proposal:
            raise ValueError("Review proposal not found")

        subject = await self._load_subject(proposal)
        feedback = self._normalize_feedback(
            await self._generate_feedback(proposal, subject),
            llm_used=self.llm.has_provider(),
        )
        proposal.status = "in_review"
        if proposal.description:
            proposal.description = (
                f"{proposal.description.rstrip()}\n\n---\nSimulated review:\n{feedback['summary']}"
            )
        else:
            proposal.description = f"Simulated review:\n{feedback['summary']}"
        await self.db.commit()
        return feedback

    async def _load_subject(self, proposal: ReviewProposal) -> dict[str, Any]:
        entity_type = proposal.entity_type
        entity_id = proposal.entity_id
        if not entity_id:
            return {"title": proposal.title, "body": proposal.description or ""}

        if entity_type == "paper":
            paper = await self.db.get(Paper, entity_id)
            if paper:
                return {
                    "title": paper.title,
                    "body": paper.abstract or "",
                    "metadata": {"year": paper.year, "venue": paper.venue},
                }
        elif entity_type == "manuscript":
            manuscript = await self.db.get(Manuscript, entity_id)
            if manuscript:
                return {
                    "title": manuscript.title,
                    "body": (manuscript.content_latex or "")[:8000],
                    "metadata": {"status": manuscript.status, "version": manuscript.version},
                }
        elif entity_type == "hypothesis":
            hypothesis = await self.db.get(Hypothesis, entity_id)
            if hypothesis:
                return {"title": "Hypothesis", "body": hypothesis.statement}
        elif entity_type == "idea":
            idea = await self.db.get(Idea, entity_id)
            if idea:
                return {"title": "Research idea", "body": idea.current_text}
        elif entity_type == "run":
            run = await self.db.get(ResearchRun, entity_id)
            if run:
                return {
                    "title": f"Research run {run.id}",
                    "body": f"State: {run.state}, phase: {run.current_phase or 'n/a'}",
                }

        return {"title": proposal.title, "body": proposal.description or ""}

    async def _generate_feedback(
        self,
        proposal: ReviewProposal,
        subject: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.llm.has_provider():
            return self._fallback_feedback(proposal, subject)

        skeptic = create_agent(AgentRole.SKEPTIC, self.llm)
        prompt = (
            f"Review proposal: {proposal.title}\n"
            f"Entity type: {proposal.entity_type}\n"
            f"Subject title: {subject.get('title', '')}\n"
            f"Subject content:\n{subject.get('body', '')[:6000]}\n\n"
            "Return JSON with keys: summary, strengths (array), weaknesses (array), "
            "questions (array), recommendation (accept|minor_revision|major_revision|reject), "
            "confidence (0-1)."
        )
        output = await skeptic.run(AgentInput(task=prompt, context={"mode": "peer_review"}))
        raw = output.result.get("response", "") or output.content
        parsed = self._parse_json(raw)
        if parsed:
            return parsed
        return self._fallback_feedback(proposal, subject, raw)

    def _parse_json(self, text: str) -> dict[str, Any] | None:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return None
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return None

    def _normalize_feedback(self, data: dict[str, Any], *, llm_used: bool) -> dict[str, Any]:
        recommendation = data.get("recommendation", "minor_revision")
        if recommendation not in {"accept", "minor_revision", "major_revision", "reject"}:
            recommendation = "minor_revision"
        confidence = data.get("confidence", 0.5)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))
        return {
            "summary": str(data.get("summary", "")).strip() or "Simulated peer review completed.",
            "strengths": list(data.get("strengths") or []),
            "weaknesses": list(data.get("weaknesses") or []),
            "questions": list(data.get("questions") or []),
            "recommendation": recommendation,
            "confidence": confidence,
            "simulated": True,
            "llm_used": llm_used,
        }

    def _fallback_feedback(
        self,
        proposal: ReviewProposal,
        subject: dict[str, Any],
        raw: str = "",
    ) -> dict[str, Any]:
        title = subject.get("title") or proposal.title
        body = (subject.get("body") or "").strip()
        weaknesses = []
        if len(body) < 120:
            weaknesses.append("Insufficient detail to evaluate methodology and evidence.")
        if proposal.entity_type == "manuscript" and "\\section" not in body:
            weaknesses.append("Manuscript structure may be incomplete (missing clear sections).")
        if not weaknesses:
            weaknesses.append("Claims should be tied to reproducible evidence and baselines.")

        summary = raw.strip() or (
            f"Template peer review for '{title}': strengthen methods, clarify contributions, "
            "and address limitations before approval."
        )
        return {
            "summary": summary,
            "strengths": ["Clear review target identified", "Topic aligns with project scope"],
            "weaknesses": weaknesses,
            "questions": [
                "What baseline comparisons support the main claims?",
                "Which artifacts will be released for reproducibility?",
            ],
            "recommendation": "minor_revision",
            "confidence": 0.55,
            "simulated": True,
            "llm_used": False,
        }
