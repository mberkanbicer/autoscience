"""Research question generation engine."""

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import structlog

from ..llm.base import Message
from ..llm.router import LLMRouter
from ..engine.conflict_detection import Conflict, Gap

logger = structlog.get_logger()


@dataclass
class ResearchQuestion:
    """A generated research question."""

    id: str
    question: str
    source_conflicts: list[str] = field(default_factory=list)
    source_gaps: list[str] = field(default_factory=list)
    novelty_score: float = 0.5
    feasibility_score: float = 0.5
    evidence_score: float = 0.5
    overall_score: float = 0.5
    rationale: str = ""
    status: str = "generated"  # generated, selected, rejected, hypothesis_created
    rejection_reason: str | None = None


@dataclass
class QuestionGenerationResult:
    """Result from question generation."""

    questions: list[ResearchQuestion] = field(default_factory=list)
    rejected_questions: list[ResearchQuestion] = field(default_factory=list)
    generation_notes: str = ""
    total_generated: int = 0
    total_selected: int = 0
    total_rejected: int = 0


class QuestionGenerationEngine:
    """Engine for generating research questions from conflicts and gaps."""

    def __init__(self, llm_router: LLMRouter):
        self.llm = llm_router

    async def generate_questions(
        self,
        conflicts: list[Conflict],
        gaps: list[Gap],
        idea_context: str,
        max_questions: int = 15,
    ) -> QuestionGenerationResult:
        """Generate research questions from conflicts and gaps."""
        all_questions = []

        # Generate questions from conflicts
        if conflicts:
            conflict_questions = await self._generate_from_conflicts(conflicts, idea_context)
            all_questions.extend(conflict_questions)

        # Generate questions from gaps
        if gaps:
            gap_questions = await self._generate_from_gaps(gaps, idea_context)
            all_questions.extend(gap_questions)

        # Generate cross-domain questions
        cross_domain_questions = await self._generate_cross_domain_questions(
            conflicts, gaps, idea_context
        )
        all_questions.extend(cross_domain_questions)

        # Deduplicate questions
        deduplicated = self._deduplicate_questions(all_questions)

        # Score questions
        scored = await self._score_questions(deduplicated, idea_context)

        # Select top questions
        selected, rejected = self._select_questions(scored, max_questions)

        # Generate notes
        notes = await self._generate_notes(selected, rejected, conflicts, gaps)

        return QuestionGenerationResult(
            questions=selected,
            rejected_questions=rejected,
            generation_notes=notes,
            total_generated=len(deduplicated),
            total_selected=len(selected),
            total_rejected=len(rejected),
        )

    async def _generate_from_conflicts(
        self,
        conflicts: list[Conflict],
        idea_context: str,
    ) -> list[ResearchQuestion]:
        """Generate questions from conflicts."""
        conflicts_summary = "\n".join(
            [
                f"Conflict {i+1} [{c.conflict_type}] (severity: {c.severity:.2f}):\n"
                f"  {c.description}\n"
                f"  Research opportunity: {c.research_opportunity}"
                for i, c in enumerate(conflicts[:10])
            ]
        )

        system = """You are a research question generator.

Generate research questions that could resolve scientific conflicts.

Output a JSON object with:
- questions: Array of question objects, each with:
  - question: The research question (string)
  - source_conflict_indices: Which conflicts motivated this question (array of ints, 0-indexed)
  - rationale: Why this question is worth investigating (string)

Guidelines:
- Questions should be specific and testable
- Questions should address the root cause of conflicts
- Questions should be answerable through research
- Generate diverse questions covering different aspects"""

        user = f"""Idea context: {idea_context}

Conflicts:
{conflicts_summary}

Generate research questions that could resolve these conflicts."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        questions = []
        for q in result.data.get("questions", []):
            source_ids = [
                conflicts[i].id
                for i in q.get("source_conflict_indices", [])
                if 0 <= i < len(conflicts)
            ]
            questions.append(
                ResearchQuestion(
                    id=str(uuid4()),
                    question=q.get("question", ""),
                    source_conflicts=source_ids,
                    rationale=q.get("rationale", ""),
                )
            )

        return questions

    async def _generate_from_gaps(
        self,
        gaps: list[Gap],
        idea_context: str,
    ) -> list[ResearchQuestion]:
        """Generate questions from research gaps."""
        gaps_summary = "\n".join(
            [
                f"Gap {i+1} [{g.gap_type}] (severity: {g.severity:.2f}):\n"
                f"  {g.description}\n"
                f"  Opportunity: {g.opportunity}"
                for i, g in enumerate(gaps[:10])
            ]
        )

        system = """You are a research question generator.

Generate research questions that address research gaps.

Output a JSON object with:
- questions: Array of question objects, each with:
  - question: The research question (string)
  - source_gap_indices: Which gaps motivated this question (array of ints, 0-indexed)
  - rationale: Why this question is worth investigating (string)

Guidelines:
- Questions should directly address identified gaps
- Questions should be specific and actionable
- Questions should lead to meaningful contributions"""

        user = f"""Idea context: {idea_context}

Research gaps:
{gaps_summary}

Generate research questions that address these gaps."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        questions = []
        for q in result.data.get("questions", []):
            source_ids = [
                gaps[i].id
                for i in q.get("source_gap_indices", [])
                if 0 <= i < len(gaps)
            ]
            questions.append(
                ResearchQuestion(
                    id=str(uuid4()),
                    question=q.get("question", ""),
                    source_gaps=source_ids,
                    rationale=q.get("rationale", ""),
                )
            )

        return questions

    async def _generate_cross_domain_questions(
        self,
        conflicts: list[Conflict],
        gaps: list[Gap],
        idea_context: str,
    ) -> list[ResearchQuestion]:
        """Generate cross-domain research questions."""
        system = """You are a cross-domain research question generator.

Generate research questions that connect ideas from different domains or fields.

Output a JSON object with:
- questions: Array of question objects, each with:
  - question: The research question (string)
  - rationale: Why this cross-domain question is interesting (string)

Guidelines:
- Questions should combine insights from different fields
- Questions should be novel and non-obvious
- Questions should be testable and specific"""

        user = f"""Idea context: {idea_context}

Generate cross-domain research questions that could lead to novel insights."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        questions = []
        for q in result.data.get("questions", []):
            questions.append(
                ResearchQuestion(
                    id=str(uuid4()),
                    question=q.get("question", ""),
                    rationale=q.get("rationale", ""),
                )
            )

        return questions

    def _deduplicate_questions(
        self,
        questions: list[ResearchQuestion],
    ) -> list[ResearchQuestion]:
        """Deduplicate similar questions."""
        if not questions:
            return []

        unique = []
        seen_questions = set()

        for q in questions:
            # Normalize question for comparison
            normalized = q.question.lower().strip()
            normalized = normalized.rstrip("?")

            if normalized not in seen_questions:
                seen_questions.add(normalized)
                unique.append(q)

        return unique

    async def _score_questions(
        self,
        questions: list[ResearchQuestion],
        idea_context: str,
    ) -> list[ResearchQuestion]:
        """Score questions on novelty, feasibility, and evidence."""
        if not questions:
            return []

        questions_summary = "\n".join(
            [
                f"{i+1}. {q.question}"
                for i, q in enumerate(questions[:15])
            ]
        )

        system = """You are a research question evaluator.

Score each research question on multiple dimensions.

Output a JSON object with:
- scores: Array of score objects, each with:
  - index: Question number (1-indexed)
  - novelty: How novel is this question (0-1)
  - feasibility: How feasible is it to answer (0-1)
  - evidence: How well supported by existing evidence (0-1)
  - rationale: Brief scoring rationale (string)

Guidelines:
- Novelty: 1 = very novel, 0 = well-studied
- Feasibility: 1 = easy to answer, 0 = very difficult
- Evidence: 1 = strong evidence available, 0 = no evidence"""

        user = f"""Idea context: {idea_context}

Questions to evaluate:
{questions_summary}

Score each question as JSON."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        # Apply scores
        for score_data in result.data.get("scores", []):
            idx = score_data.get("index", 1) - 1
            if 0 <= idx < len(questions):
                questions[idx].novelty_score = score_data.get("novelty", 0.5)
                questions[idx].feasibility_score = score_data.get("feasibility", 0.5)
                questions[idx].evidence_score = score_data.get("evidence", 0.5)
                questions[idx].rationale = score_data.get("rationale", "")

        # Calculate overall score
        for q in questions:
            q.overall_score = (
                0.4 * q.novelty_score
                + 0.3 * q.feasibility_score
                + 0.3 * q.evidence_score
            )

        # Sort by overall score
        questions.sort(key=lambda q: q.overall_score, reverse=True)

        return questions

    def _select_questions(
        self,
        questions: list[ResearchQuestion],
        max_questions: int,
    ) -> tuple[list[ResearchQuestion], list[ResearchQuestion]]:
        """Select top questions and reject others."""
        if len(questions) <= max_questions:
            for q in questions:
                q.status = "selected"
            return questions, []

        selected = questions[:max_questions]
        rejected = questions[max_questions:]

        for q in selected:
            q.status = "selected"
        for q in rejected:
            q.status = "rejected"
            q.rejection_reason = "Score below threshold"

        return selected, rejected

    async def _generate_notes(
        self,
        selected: list[ResearchQuestion],
        rejected: list[ResearchQuestion],
        conflicts: list[Conflict],
        gaps: list[Gap],
    ) -> str:
        """Generate notes about question generation."""
        selected_summary = "\n".join(
            [f"- {q.question[:100]}..." for q in selected[:5]]
        )

        system = """You are a research strategy documenter.

Given generated research questions, provide brief notes on:
1. Overview of generated questions
2. Key themes
3. Most promising directions
4. Recommendations

Keep it concise (2-3 paragraphs)."""

        user = f"""Generated {len(selected)} questions from {len(conflicts)} conflicts and {len(gaps)} gaps.
Rejected {len(rejected)} questions.

Top selected questions:
{selected_summary}

Provide notes on the generated questions."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete(messages, temperature=0.3, max_tokens=500)
        return result.content
