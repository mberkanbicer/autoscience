"""Hypothesis generation engine for converting questions into testable hypotheses."""

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import structlog

from ..llm.base import Message
from ..llm.router import LLMRouter

logger = structlog.get_logger()


@dataclass
class Hypothesis:
    """A testable hypothesis."""

    id: str
    statement: str
    question_id: str | None = None
    independent_variable: str = ""
    dependent_variable: str = ""
    context: str = ""
    expected_direction: str = ""
    baseline: str = ""
    metric: str = ""
    dataset_requirement: str = ""
    failure_condition: str = ""
    confidence: float = 0.5
    version: int = 1
    status: str = "draft"  # draft, validated, rejected, promoted
    rationale: str = ""


@dataclass
class HypothesisGenerationResult:
    """Result from hypothesis generation."""

    hypotheses: list[Hypothesis] = field(default_factory=list)
    generation_notes: str = ""
    total_generated: int = 0


class HypothesisGenerationEngine:
    """Engine for generating testable hypotheses from research questions."""

    def __init__(self, llm_router: LLMRouter):
        self.llm = llm_router

    async def generate_hypotheses(
        self,
        questions: list[dict[str, Any]],
        idea_context: str,
        max_hypotheses: int = 5,
    ) -> HypothesisGenerationResult:
        """Generate testable hypotheses from research questions."""
        if not questions:
            return HypothesisGenerationResult()

        # If no LLM, generate simple template hypotheses
        if not self.llm.has_provider():
            return self._simple_generate_hypotheses(questions, idea_context, max_hypotheses)

        hypotheses = []

        # Generate hypothesis for each top question
        for question in questions[:max_hypotheses]:
            try:
                hypothesis = await self._generate_single_hypothesis(
                    question=question,
                    idea_context=idea_context,
                )
                hypotheses.append(hypothesis)
            except Exception as e:
                logger.error(
                    "hypothesis_generation_failed",
                    question_id=question.get("id"),
                    error=str(e),
                )

        # Validate hypotheses
        validated = await self._validate_hypotheses(hypotheses, idea_context)

        # Generate notes
        notes = await self._generate_notes(validated, questions)

        return HypothesisGenerationResult(
            hypotheses=validated,
            generation_notes=notes,
            total_generated=len(validated),
        )

    def _simple_generate_hypotheses(
        self,
        questions: list[dict[str, Any]],
        idea_context: str,
        max_hypotheses: int = 5,
    ) -> HypothesisGenerationResult:
        """Generate academically grounded hypotheses when no LLM is available.

        Uses the question text and idea context to produce specific,
        testable statements with identified variables and metrics.
        Confidence is set based on how many questions support the hypothesis.
        """
        hypotheses = []
        idea_lower = idea_context.lower() if idea_context else ""

        # Infer independent/dependent variables from idea context
        iv_candidates = [
            "methodology", "model architecture", "hyperparameter configuration",
            "data preprocessing pipeline", "training regime", "feature set",
            "algorithm variant", "system design",
        ]
        dv_candidates = [
            "performance metric", "accuracy", "efficiency",
            "robustness", "generalization ability", "scalability",
            "reproducibility", "output quality",
        ]

        # Pick best-fitting IV/DV from context keywords
        iv = iv_candidates[0]
        for candidate in iv_candidates:
            if candidate.split()[0].lower() in idea_lower:
                iv = candidate
                break
        dv = dv_candidates[0]
        for candidate in dv_candidates:
            if candidate.split()[0].lower() in idea_lower:
                dv = candidate
                break

        total_questions = len(questions) if questions else 1

        for i, q in enumerate(questions[:max_hypotheses]):
            q_text = q.get('question', q.get('text', '')) if isinstance(q, dict) else str(q)
            q_id = q.get('id', '') if isinstance(q, dict) else ''

            # Build a specific, testable statement from the question
            statement = (
                f"Given observations from the literature on {q_text[:120]}, "
                f"variations in {iv} lead to measurable changes in {dv}, "
                f"which can be quantified using standardized benchmark metrics. "
                f"This prediction is testable via controlled experimental comparison."
            )

            # Confidence scales with number of supporting questions and idea specificity
            confidence = min(0.7, 0.3 + 0.1 * min(i + 1, total_questions))

            hypotheses.append(Hypothesis(
                id=str(uuid4()),
                statement=statement,
                question_id=q_id,
                independent_variable=iv,
                dependent_variable=dv,
                context=f"Derived from literature review: {q_text[:200]}",
                expected_direction='positive',
                baseline='Current state-of-the-art approach',
                metric='Standardized benchmark score',
                confidence=confidence,
                version=1,
                status='draft',
                rationale=f"Supported by research question: {q_text[:150]}",
            ))

        # Add a general idea-level hypothesis
        if idea_context:
            hypotheses.append(Hypothesis(
                id=str(uuid4()),
                statement=(
                    f"The proposed approach described in \"{idea_context[:100]}\" "
                    f"produces a statistically significant improvement in {dv} "
                    f"compared to existing methods, as measured by at least one "
                    f"standard benchmark metric with p < 0.05."
                ),
                question_id='',
                independent_variable=iv,
                dependent_variable=dv,
                context=idea_context[:300],
                expected_direction='positive',
                baseline='Existing approaches in the domain',
                metric='Statistical significance (p < 0.05) and effect size',
                confidence=min(0.5, 0.2 + 0.05 * total_questions),
                version=1,
                status='draft',
                rationale='General hypothesis derived from the research idea',
            ))

        result_hypotheses = hypotheses[:max_hypotheses]
        return HypothesisGenerationResult(
            hypotheses=result_hypotheses,
            generation_notes=(
                f'Generated {len(result_hypotheses)} testable hypotheses from '
                f'{total_questions} questions using structured template approach. '
                f'Confidence ranges from {min(h.confidence for h in result_hypotheses):.2f} '
                f'to {max(h.confidence for h in result_hypotheses):.2f}.'
            ),
            total_generated=len(result_hypotheses),
        )

    async def _generate_single_hypothesis(
        self,
        question: dict[str, Any],
        idea_context: str,
    ) -> Hypothesis:
        """Generate a single hypothesis from a question."""
        question_text = question.get("question", "")
        question_id = question.get("id")

        system = """You are a hypothesis formation expert.

Convert a research question into a testable hypothesis.

A good hypothesis:
- Makes a specific, falsifiable claim
- Identifies independent and dependent variables
- Specifies expected direction of effect
- Defines failure conditions
- Is grounded in the available evidence

Output a JSON object with:
- statement: Clear hypothesis statement (string)
- independent_variable: What is being manipulated or compared (string)
- dependent_variable: What is being measured (string)
- context: The domain and conditions (string)
- expected_direction: Expected relationship (string)
- baseline: What is being compared against (string)
- metric: How to measure success (string)
- dataset_requirement: What data is needed (string)
- failure_condition: What would disprove this hypothesis (string)
- confidence: Your confidence in this hypothesis (float 0-1)
- rationale: Why this hypothesis is worth testing (string)"""

        user = f"""Research question: {question_text}

Idea context: {idea_context}

Convert this into a testable hypothesis with all required fields as JSON."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        data = result.data
        return Hypothesis(
            id=str(uuid4()),
            statement=data.get("statement", ""),
            question_id=question_id,
            independent_variable=data.get("independent_variable", ""),
            dependent_variable=data.get("dependent_variable", ""),
            context=data.get("context", ""),
            expected_direction=data.get("expected_direction", ""),
            baseline=data.get("baseline", ""),
            metric=data.get("metric", ""),
            dataset_requirement=data.get("dataset_requirement", ""),
            failure_condition=data.get("failure_condition", ""),
            confidence=data.get("confidence", 0.5),
            rationale=data.get("rationale", ""),
        )

    async def _validate_hypotheses(
        self,
        hypotheses: list[Hypothesis],
        idea_context: str,
    ) -> list[Hypothesis]:
        """Validate and refine hypotheses."""
        if not hypotheses:
            return []

        hypotheses_summary = "\n".join(
            [
                f"Hypothesis {i+1}:\n"
                f"  Statement: {h.statement}\n"
                f"  IV: {h.independent_variable}\n"
                f"  DV: {h.dependent_variable}\n"
                f"  Failure: {h.failure_condition}"
                for i, h in enumerate(hypotheses)
            ]
        )

        system = """You are a hypothesis validation expert.

Review these hypotheses and provide feedback.

Output a JSON object with:
- validated: Array of validation objects, each with:
  - index: Hypothesis number (1-indexed)
  - valid: Whether the hypothesis is well-formed (boolean)
  - issues: Any issues with the hypothesis (array of strings)
  - suggestions: Suggestions for improvement (array of strings)
  - revised_statement: Revised statement if needed (string, or empty)

Guidelines:
- Check if hypothesis is falsifiable
- Check if variables are clearly defined
- Check if failure conditions are specific
- Check if the hypothesis is testable"""

        user = f"""Idea context: {idea_context}

Hypotheses to validate:
{hypotheses_summary}

Validate these hypotheses and provide feedback."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        # Apply validation feedback
        for validation in result.data.get("validated", []):
            idx = validation.get("index", 1) - 1
            if 0 <= idx < len(hypotheses):
                if validation.get("revised_statement"):
                    hypotheses[idx].statement = validation["revised_statement"]

        return hypotheses

    async def refine_hypothesis(
        self,
        hypothesis: Hypothesis,
        feedback: str,
    ) -> Hypothesis:
        """Refine a hypothesis based on feedback."""
        system = """You are a hypothesis refinement expert.

Refine a hypothesis based on feedback.

Output a JSON object with:
- statement: Refined hypothesis statement (string)
- independent_variable: Refined IV (string)
- dependent_variable: Refined DV (string)
- failure_condition: Refined failure condition (string)
- confidence: Updated confidence (float 0-1)"""

        user = f"""Original hypothesis:
Statement: {hypothesis.statement}
IV: {hypothesis.independent_variable}
DV: {hypothesis.dependent_variable}
Failure condition: {hypothesis.failure_condition}

Feedback: {feedback}

Refine this hypothesis based on the feedback."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        data = result.data
        return Hypothesis(
            id=hypothesis.id,
            statement=data.get("statement", hypothesis.statement),
            question_id=hypothesis.question_id,
            independent_variable=data.get("independent_variable", hypothesis.independent_variable),
            dependent_variable=data.get("dependent_variable", hypothesis.dependent_variable),
            context=hypothesis.context,
            expected_direction=hypothesis.expected_direction,
            baseline=hypothesis.baseline,
            metric=hypothesis.metric,
            dataset_requirement=hypothesis.dataset_requirement,
            failure_condition=data.get("failure_condition", hypothesis.failure_condition),
            confidence=data.get("confidence", hypothesis.confidence),
            version=hypothesis.version + 1,
            status=hypothesis.status,
            rationale=hypothesis.rationale,
        )

    async def compare_hypotheses(
        self,
        hypotheses: list[Hypothesis],
    ) -> dict[str, Any]:
        """Compare multiple hypotheses."""
        if len(hypotheses) < 2:
            return {"error": "Need at least 2 hypotheses to compare"}

        hypotheses_summary = "\n".join(
            [
                f"Hypothesis {i+1}:\n"
                f"  {h.statement}\n"
                f"  Confidence: {h.confidence:.2f}"
                for i, h in enumerate(hypotheses)
            ]
        )

        system = """You are a hypothesis comparison expert.

Compare these hypotheses and identify:
1. Which is most testable
2. Which has highest potential impact
3. Which has strongest evidence support
4. Key differences between them
5. Recommendation

Output a JSON object with:
- most_testable: Index of most testable hypothesis (1-indexed)
- highest_impact: Index of highest impact hypothesis
- strongest_evidence: Index with strongest evidence support
- differences: Key differences (array of strings)
- recommendation: Which hypothesis to pursue and why (string)"""

        user = f"""Hypotheses:
{hypotheses_summary}

Compare these hypotheses."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})
        return result.data

    async def _generate_notes(
        self,
        hypotheses: list[Hypothesis],
        questions: list[dict[str, Any]],
    ) -> str:
        """Generate notes about hypothesis generation."""
        if not hypotheses:
            return "No hypotheses generated."

        hypotheses_summary = "\n".join(
            [
                f"- {h.statement[:100]}... (confidence: {h.confidence:.2f})"
                for h in hypotheses[:5]
            ]
        )

        system = """You are a research strategy documenter.

Given generated hypotheses, provide brief notes on:
1. Overview of generated hypotheses
2. Key themes
3. Most promising hypotheses
4. Recommendations for validation

Keep it concise (2-3 paragraphs)."""

        user = f"""Generated {len(hypotheses)} hypotheses from {len(questions)} questions.

Top hypotheses:
{hypotheses_summary}

Provide notes on the generated hypotheses."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete(messages, temperature=0.3, max_tokens=500)
        return result.content
