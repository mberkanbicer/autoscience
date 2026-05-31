"""Idea scoring engine for evaluating ideas on multiple dimensions."""

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import structlog

from ..llm.base import Message
from ..llm.router import LLMRouter

logger = structlog.get_logger()


@dataclass
class IdeaScore:
    """Score for an idea across multiple dimensions."""

    idea_id: str
    novelty: float = 5.0
    feasibility: float = 5.0
    importance: float = 5.0
    evidence_support: float = 5.0
    validation_clarity: float = 5.0
    differentiation: float = 5.0
    data_availability: float = 5.0
    skill_leverage: float = 5.0
    user_alignment: float = 5.0
    prior_art_risk: float = 5.0
    safety_risk: float = 5.0
    cost_risk: float = 5.0
    overall_value: float = 5.0
    classification: str = "incremental"
    rationale: str = ""


@dataclass
class ScoringResult:
    """Result from idea scoring."""

    scores: list[IdeaScore] = field(default_factory=list)
    scoring_notes: str = ""
    total_scored: int = 0


class IdeaScoringEngine:
    """Engine for scoring and classifying ideas."""

    def __init__(self, llm_router: LLMRouter):
        self.llm = llm_router

    # Scoring weights from blueprint
    WEIGHTS = {
        "novelty": 0.18,
        "feasibility": 0.14,
        "importance": 0.14,
        "evidence_support": 0.12,
        "validation_clarity": 0.14,
        "differentiation": 0.12,
        "data_availability": 0.08,
        "skill_leverage": 0.05,
        "user_alignment": 0.03,
        "prior_art_risk": -0.15,  # Negative weight (risk)
        "safety_risk": -0.05,  # Negative weight (risk)
        "cost_risk": -0.03,  # Negative weight (risk)
    }

    # Classification thresholds
    THRESHOLDS = {
        "high_value": 8.0,
        "promising": 6.5,
        "incremental": 5.0,
        "weak": 3.5,
        "reject": 0.0,
    }

    async def score_idea(
        self,
        idea: dict[str, Any],
        papers: list[dict[str, Any]] | None = None,
        conflicts: list[dict[str, Any]] | None = None,
        validation_plan: dict[str, Any] | None = None,
    ) -> IdeaScore:
        """Score an idea on all dimensions."""
        idea_id = idea.get("id", str(uuid4()))
        idea_text = idea.get("current_text") or idea.get("text", "")

        # If no LLM, use metadata-based scoring
        if not self.llm.has_provider():
            return self._simple_score(idea_id, idea_text, papers, conflicts)

        # Get LLM scores
        scores_data = await self._llm_score(
            idea_text=idea_text,
            papers=papers,
            conflicts=conflicts,
            validation_plan=validation_plan,
        )

        # Create score object
        score = IdeaScore(
            idea_id=idea_id,
            novelty=scores_data.get("novelty", 5.0),
            feasibility=scores_data.get("feasibility", 5.0),
            importance=scores_data.get("importance", 5.0),
            evidence_support=scores_data.get("evidence_support", 5.0),
            validation_clarity=scores_data.get("validation_clarity", 5.0),
            differentiation=scores_data.get("differentiation", 5.0),
            data_availability=scores_data.get("data_availability", 5.0),
            skill_leverage=scores_data.get("skill_leverage", 5.0),
            user_alignment=scores_data.get("user_alignment", 5.0),
            prior_art_risk=scores_data.get("prior_art_risk", 5.0),
            safety_risk=scores_data.get("safety_risk", 5.0),
            cost_risk=scores_data.get("cost_risk", 5.0),
            rationale=scores_data.get("rationale", ""),
        )

        # Calculate overall value
        score.overall_value = self._calculate_overall_value(score)

        # Classify idea
        score.classification = self._classify(score.overall_value)

        return score

    def _simple_score(self, idea_id: str, idea_text: str, papers: list | None, conflicts: list | None) -> IdeaScore:
        """Simple metadata-based scoring when no LLM is available."""
        # Base scores
        novelty = 5.0
        feasibility = 6.0
        importance = 5.0
        evidence = 4.0 if papers and len(papers) > 5 else 3.0
        validation = 4.0
        differentiation = 5.0
        data_avail = 5.0 if papers and len(papers) > 0 else 3.0
        skill = 5.0
        user_align = 7.0
        prior_art = 4.0 if conflicts and len(conflicts) > 0 else 5.0
        safety = 7.0
        cost = 6.0

        score = IdeaScore(
            idea_id=idea_id,
            novelty=novelty,
            feasibility=feasibility,
            importance=importance,
            evidence_support=evidence,
            validation_clarity=validation,
            differentiation=differentiation,
            data_availability=data_avail,
            skill_leverage=skill,
            user_alignment=user_align,
            prior_art_risk=prior_art,
            safety_risk=safety,
            cost_risk=cost,
            rationale='Simple metadata-based scoring (no LLM available)',
        )
        score.overall_value = self._calculate_overall_value(score)
        score.classification = self._classify(score.overall_value)
        return score

    async def score_ideas(
        self,
        ideas: list[dict[str, Any]],
        papers: list[dict[str, Any]] | None = None,
        conflicts: list[dict[str, Any]] | None = None,
    ) -> ScoringResult:
        """Score multiple ideas."""
        scores = []

        for idea in ideas:
            try:
                score = await self.score_idea(idea, papers, conflicts)
                scores.append(score)
            except Exception as e:
                logger.error(
                    "idea_scoring_failed",
                    idea_id=idea.get("id"),
                    error=str(e),
                )

        # Sort by overall value
        scores.sort(key=lambda s: s.overall_value, reverse=True)

        # Generate notes
        notes = await self._generate_notes(scores)

        return ScoringResult(
            scores=scores,
            scoring_notes=notes,
            total_scored=len(scores),
        )

    async def _llm_score(
        self,
        idea_text: str,
        papers: list[dict[str, Any]] | None = None,
        conflicts: list[dict[str, Any]] | None = None,
        validation_plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Use LLM to score an idea."""
        context_parts = []

        if papers:
            papers_summary = "\n".join(
                [f"- {p.get('title', 'Unknown')}" for p in papers[:10]]
            )
            context_parts.append(f"Relevant papers:\n{papers_summary}")

        if conflicts:
            conflicts_summary = "\n".join(
                [f"- [{c.get('type')}] {c.get('description', '')[:100]}" for c in conflicts[:5]]
            )
            context_parts.append(f"Conflicts identified:\n{conflicts_summary}")

        if validation_plan:
            context_parts.append(
                f"Validation feasibility: {validation_plan.get('feasibility_score', 'Unknown')}"
            )

        context = "\n\n".join(context_parts) if context_parts else "No additional context."

        system = """You are an idea scoring expert.

Score this research idea on multiple dimensions (0-10 scale).

Dimensions:
- novelty: How original is this idea? (0 = well-known, 10 = truly novel)
- feasibility: How realistic is this to implement? (0 = impossible, 10 = straightforward)
- importance: How significant is the problem? (0 = trivial, 10 = critical)
- evidence_support: How well supported by existing literature? (0 = no support, 10 = strong support)
- validation_clarity: How clearly can this be tested? (0 = vague, 10 = crystal clear)
- differentiation: How different from existing work? (0 = duplicate, 10 = unique approach)
- data_availability: How available is the needed data? (0 = unavailable, 10 = freely available)
- skill_leverage: How much can existing skills help? (0 = none, 10 = directly applicable)
- user_alignment: How aligned with user goals? (0 = misaligned, 10 = perfect match)
- prior_art_risk: Risk of overlapping with existing work (0 = high risk, 10 = no risk)
- safety_risk: Risk of negative consequences (0 = high risk, 10 = no risk)
- cost_risk: Resource cost risk (0 = very expensive, 10 = very cheap)

Output a JSON object with all scores (0-10) and a rationale."""

        user = f"""Idea: {idea_text}

Context:
{context}

Score this idea on all dimensions as JSON."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})
        return result.data

    def _calculate_overall_value(self, score: IdeaScore) -> float:
        """Calculate overall value using weighted formula."""
        overall = (
            self.WEIGHTS["novelty"] * score.novelty
            + self.WEIGHTS["feasibility"] * score.feasibility
            + self.WEIGHTS["importance"] * score.importance
            + self.WEIGHTS["evidence_support"] * score.evidence_support
            + self.WEIGHTS["validation_clarity"] * score.validation_clarity
            + self.WEIGHTS["differentiation"] * score.differentiation
            + self.WEIGHTS["data_availability"] * score.data_availability
            + self.WEIGHTS["skill_leverage"] * score.skill_leverage
            + self.WEIGHTS["user_alignment"] * score.user_alignment
            + self.WEIGHTS["prior_art_risk"] * score.prior_art_risk
            + self.WEIGHTS["safety_risk"] * score.safety_risk
            + self.WEIGHTS["cost_risk"] * score.cost_risk
        )

        # Normalize to 0-10 scale
        # Max possible: 0.18*10 + 0.14*10 + 0.14*10 + 0.12*10 + 0.14*10 + 0.12*10 + 0.08*10 + 0.05*10 + 0.03*10 - 0.15*0 - 0.05*0 - 0.03*0 = 10
        # Min possible: 0.18*0 + ... - 0.15*10 - 0.05*10 - 0.03*10 = -2.3
        # Scale: (value - min) / (max - min) * 10
        min_possible = -2.3
        max_possible = 10.0
        normalized = ((overall - min_possible) / (max_possible - min_possible)) * 10
        return round(max(0, min(10, normalized)), 2)

    def _classify(self, overall_value: float) -> str:
        """Classify idea based on overall value."""
        if overall_value >= self.THRESHOLDS["high_value"]:
            return "high_value"
        elif overall_value >= self.THRESHOLDS["promising"]:
            return "promising"
        elif overall_value >= self.THRESHOLDS["incremental"]:
            return "incremental"
        elif overall_value >= self.THRESHOLDS["weak"]:
            return "weak"
        else:
            return "reject"

    async def _generate_notes(self, scores: list[IdeaScore]) -> str:
        """Generate notes about scoring results."""
        if not scores:
            return "No ideas scored."

        top_ideas = scores[:5]
        top_summary = "\n".join(
            [
                f"- {s.classification}: {s.overall_value:.2f} (novelty={s.novelty:.1f}, feasibility={s.feasibility:.1f})"
                for s in top_ideas
            ]
        )

        # Count by classification
        classifications = {}
        for s in scores:
            classifications[s.classification] = classifications.get(s.classification, 0) + 1

        class_summary = ", ".join([f"{k}: {v}" for k, v in classifications.items()])

        system = """You are a research strategy documenter.

Given scored ideas, provide brief notes on:
1. Overview of scoring results
2. Distribution of classifications
3. Top performing ideas
4. Common strengths and weaknesses
5. Recommendations

Keep it concise (2-3 paragraphs)."""

        user = f"""Scored {len(scores)} ideas.

Classification distribution: {class_summary}

Top ideas:
{top_summary}

Provide notes on the scoring results."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete(messages, temperature=0.3, max_tokens=500)
        return result.content

    def get_scoring_breakdown(self, score: IdeaScore) -> dict[str, Any]:
        """Get detailed scoring breakdown."""
        return {
            "idea_id": score.idea_id,
            "overall_value": score.overall_value,
            "classification": score.classification,
            "dimensions": {
                "novelty": {"score": score.novelty, "weight": self.WEIGHTS["novelty"]},
                "feasibility": {"score": score.feasibility, "weight": self.WEIGHTS["feasibility"]},
                "importance": {"score": score.importance, "weight": self.WEIGHTS["importance"]},
                "evidence_support": {"score": score.evidence_support, "weight": self.WEIGHTS["evidence_support"]},
                "validation_clarity": {"score": score.validation_clarity, "weight": self.WEIGHTS["validation_clarity"]},
                "differentiation": {"score": score.differentiation, "weight": self.WEIGHTS["differentiation"]},
                "data_availability": {"score": score.data_availability, "weight": self.WEIGHTS["data_availability"]},
                "skill_leverage": {"score": score.skill_leverage, "weight": self.WEIGHTS["skill_leverage"]},
                "user_alignment": {"score": score.user_alignment, "weight": self.WEIGHTS["user_alignment"]},
                "prior_art_risk": {"score": score.prior_art_risk, "weight": self.WEIGHTS["prior_art_risk"]},
                "safety_risk": {"score": score.safety_risk, "weight": self.WEIGHTS["safety_risk"]},
                "cost_risk": {"score": score.cost_risk, "weight": self.WEIGHTS["cost_risk"]},
            },
            "rationale": score.rationale,
        }
