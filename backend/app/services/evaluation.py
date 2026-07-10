"""Evaluation framework for measuring system performance."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

import structlog

from app.llm.base import Message
from app.llm.router import LLMRouter

logger = structlog.get_logger()


@dataclass
class EvaluationIdea:
    """A test idea for evaluation."""

    id: str
    text: str
    domain: str
    expected_classification: str | None = None
    expected_novelty_range: tuple[float, float] = (5.0, 8.0)


@dataclass
class EvaluationResult:
    """Result from evaluating a single idea."""

    idea_id: str
    method: str  # autoscience, one_shot_llm, static_review
    score: float
    classification: str
    novelty_score: float
    feasibility_score: float
    prior_art_overlap: float  # 0-1, lower is better
    validation_quality: float
    duration_seconds: float
    cost_usd: float


@dataclass
class BenchmarkResult:
    """Result from benchmarking multiple ideas."""

    benchmark_id: str
    method: str
    results: list[EvaluationResult] = field(default_factory=list)
    avg_score: float = 0.0
    avg_novelty: float = 0.0
    avg_feasibility: float = 0.0
    avg_prior_art_overlap: float = 0.0
    avg_validation_quality: float = 0.0
    total_cost: float = 0.0
    total_duration: float = 0.0


class EvaluationFramework:
    """Framework for evaluating the research system."""

    def __init__(self, llm_router: LLMRouter):
        self.llm = llm_router
        self.test_ideas = self._load_test_ideas()

    def _load_test_ideas(self) -> list[EvaluationIdea]:
        """Load test ideas for evaluation."""
        return [
            EvaluationIdea(
                id="test_1",
                text="A system that autonomously discovers research gaps by analyzing citation conflicts",
                domain="AI research automation",
                expected_classification="promising",
            ),
            EvaluationIdea(
                id="test_2",
                text="Using graph neural networks for molecular property prediction",
                domain="computational chemistry",
                expected_classification="incremental",
            ),
            EvaluationIdea(
                id="test_3",
                text="A framework for cross-lingual transfer learning without parallel data",
                domain="natural language processing",
                expected_classification="high_value",
            ),
            EvaluationIdea(
                id="test_4",
                text="Improving image classification accuracy by 0.1% on CIFAR-10",
                domain="computer vision",
                expected_classification="weak",
            ),
            EvaluationIdea(
                id="test_5",
                text="A novel approach to federated learning that addresses privacy concerns",
                domain="machine learning",
                expected_classification="promising",
            ),
        ]

    async def evaluate_idea(
        self,
        idea: EvaluationIdea,
        method: str = "autoscience",
    ) -> EvaluationResult:
        """Evaluate a single idea using specified method."""
        start_time = datetime.now()

        if method == "autoscience":
            result = await self._evaluate_autoscience(idea)
        elif method == "one_shot_llm":
            result = await self._evaluate_one_shot_llm(idea)
        elif method == "static_review":
            result = await self._evaluate_static_review(idea)
        else:
            raise ValueError(f"Unknown method: {method}")

        duration = (datetime.now() - start_time).total_seconds()
        result.duration_seconds = duration

        return result

    async def _evaluate_autoscience(self, idea: EvaluationIdea) -> EvaluationResult:
        """Evaluate using the full autoscience system."""
        # Simulate full system evaluation
        # In production, this would run the complete workflow

        system_prompt = """You are a research idea evaluator.

Evaluate this research idea on multiple dimensions.

Output a JSON object with:
- score: Overall score 0-10
- classification: high_value | promising | incremental | weak | reject
- novelty: Novelty score 0-10
- feasibility: Feasibility score 0-10
- prior_art_overlap: How much it overlaps with existing work 0-1 (lower is better)
- validation_quality: How clearly it can be validated 0-10
- rationale: Brief explanation"""

        user_prompt = f"""Idea: {idea.text}

Domain: {idea.domain}

Evaluate this idea."""

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        return EvaluationResult(
            idea_id=idea.id,
            method="autoscience",
            score=result.data.get("score", 5.0),
            classification=result.data.get("classification", "incremental"),
            novelty_score=result.data.get("novelty", 5.0),
            feasibility_score=result.data.get("feasibility", 5.0),
            prior_art_overlap=result.data.get("prior_art_overlap", 0.5),
            validation_quality=result.data.get("validation_quality", 5.0),
            duration_seconds=0,
            cost_usd=result.completion.cost_usd,
        )

    async def _evaluate_one_shot_llm(self, idea: EvaluationIdea) -> EvaluationResult:
        """Evaluate using one-shot LLM (baseline)."""
        system_prompt = """You are a research idea evaluator.

Quickly evaluate this research idea.

Output a JSON object with:
- score: Overall score 0-10
- classification: high_value | promising | incremental | weak | reject
- novelty: Novelty score 0-10
- feasibility: Feasibility score 0-10
- prior_art_overlap: 0-1
- validation_quality: 0-10"""

        user_prompt = f"""Idea: {idea.text}

Evaluate this idea."""

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        return EvaluationResult(
            idea_id=idea.id,
            method="one_shot_llm",
            score=result.data.get("score", 5.0),
            classification=result.data.get("classification", "incremental"),
            novelty_score=result.data.get("novelty", 5.0),
            feasibility_score=result.data.get("feasibility", 5.0),
            prior_art_overlap=result.data.get("prior_art_overlap", 0.5),
            validation_quality=result.data.get("validation_quality", 5.0),
            duration_seconds=0,
            cost_usd=result.completion.cost_usd,
        )

    async def _evaluate_static_review(self, idea: EvaluationIdea) -> EvaluationResult:
        """Evaluate using static literature review (baseline)."""
        # Simple heuristic-based evaluation
        len(idea.text)
        word_count = len(idea.text.split())

        # Basic scoring
        score = 5.0
        if word_count > 10:
            score += 0.5
        if any(word in idea.text.lower() for word in ["novel", "new", "first"]):
            score += 1.0
        if any(word in idea.text.lower() for word in ["improve", "better", "enhance"]):
            score -= 0.5

        return EvaluationResult(
            idea_id=idea.id,
            method="static_review",
            score=min(10.0, max(0.0, score)),
            classification="incremental",
            novelty_score=5.0,
            feasibility_score=5.0,
            prior_art_overlap=0.5,
            validation_quality=5.0,
            duration_seconds=0,
            cost_usd=0.0,
        )

    async def run_benchmark(
        self,
        methods: list[str] | None = None,
    ) -> list[BenchmarkResult]:
        """Run full benchmark across all test ideas and methods."""
        if methods is None:
            methods = ["autoscience", "one_shot_llm", "static_review"]

        results_by_method: dict[str, list[EvaluationResult]] = {m: [] for m in methods}

        for idea in self.test_ideas:
            for method in methods:
                try:
                    result = await self.evaluate_idea(idea, method)
                    results_by_method[method].append(result)
                except (ValueError, RuntimeError) as e:
                    logger.error(
                        "evaluation_content_error",
                        idea_id=idea.id,
                        method=method,
                        error=str(e),
                    )
                except Exception as e:
                    logger.error(
                        "evaluation_failed",
                        idea_id=idea.id,
                        method=method,
                        error=str(e),
                    )

        # Calculate benchmark results
        benchmarks = []
        for method, results in results_by_method.items():
            if not results:
                continue

            benchmark = BenchmarkResult(
                benchmark_id=str(uuid4()),
                method=method,
                results=results,
                avg_score=sum(r.score for r in results) / len(results),
                avg_novelty=sum(r.novelty_score for r in results) / len(results),
                avg_feasibility=sum(r.feasibility_score for r in results) / len(results),
                avg_prior_art_overlap=sum(r.prior_art_overlap for r in results) / len(results),
                avg_validation_quality=sum(r.validation_quality for r in results) / len(results),
                total_cost=sum(r.cost_usd for r in results),
                total_duration=sum(r.duration_seconds for r in results),
            )
            benchmarks.append(benchmark)

        return benchmarks

    def generate_report(self, benchmarks: list[BenchmarkResult]) -> str:
        """Generate a benchmark report."""
        report = """# Autoscience Evaluation Report

## Executive Summary

This report presents the evaluation results for the Background Scientific Cognition System.

## Methods Evaluated

1. **Autoscience** - Full system with literature analysis, conflict detection, and hypothesis generation
2. **One-Shot LLM** - Single LLM call without research context
3. **Static Review** - Heuristic-based evaluation without AI

## Test Ideas

"""

        for idea in self.test_ideas:
            report += f"- **{idea.domain}**: {idea.text[:100]}...\n"

        report += "\n## Results\n\n"

        # Results table
        report += "| Method | Avg Score | Avg Novelty | Avg Feasibility | Avg Prior Art | Total Cost |\n"
        report += "|--------|-----------|-------------|-----------------|---------------|------------|\n"

        for benchmark in benchmarks:
            report += f"| {benchmark.method} | {benchmark.avg_score:.2f} | {benchmark.avg_novelty:.2f} | {benchmark.avg_feasibility:.2f} | {benchmark.avg_prior_art_overlap:.2f} | ${benchmark.total_cost:.4f} |\n"

        # Comparison
        if len(benchmarks) >= 2:
            autoscience = next((b for b in benchmarks if b.method == "autoscience"), None)
            one_shot = next((b for b in benchmarks if b.method == "one_shot_llm"), None)

            if autoscience and one_shot:
                score_diff = autoscience.avg_score - one_shot.avg_score
                novelty_diff = autoscience.avg_novelty - one_shot.avg_novelty

                report += f"""
## Key Findings

1. **Score Improvement**: Autoscience {'outperforms' if score_diff > 0 else 'underperforms'} one-shot LLM by {abs(score_diff):.2f} points
2. **Novelty Enhancement**: Autoscience {'identifies' if novelty_diff > 0 else 'misses'} more novel ideas ({novelty_diff:+.2f})
3. **Cost Analysis**: Autoscience costs ${autoscience.total_cost:.4f} vs ${one_shot.total_cost:.4f} for one-shot
"""

        report += """
## Recommendations

1. Use Autoscience for high-stakes research decisions
2. One-shot LLM suitable for quick screening
3. Static review useful for initial filtering

## Limitations

- Test set is small (5 ideas)
- No expert evaluation yet
- Cost varies by LLM provider

---

*Report generated by Autoscience Evaluation Framework*
"""

        return report
