"""Validation planning engine for designing experiments to test hypotheses."""

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import structlog

from app.llm.base import Message
from app.llm.router import LLMRouter

logger = structlog.get_logger()


@dataclass
class DatasetCandidate:
    """A candidate dataset for validation."""

    name: str
    source: str
    url: str | None = None
    description: str = ""
    size: str = ""
    format: str = ""
    relevance_score: float = 0.5


@dataclass
class ValidationPlan:
    """A plan for validating a hypothesis."""

    id: str
    hypothesis_id: str
    dataset_candidates: list[DatasetCandidate] = field(default_factory=list)
    benchmark_candidates: list[str] = field(default_factory=list)
    baselines: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    experimental_design: str = ""
    statistical_tests: list[str] = field(default_factory=list)
    simulation_option: str | None = None
    expected_artifacts: list[str] = field(default_factory=list)
    difficulty_estimate: float = 0.5  # 0-1 (1 = very difficult)
    cost_estimate: float = 0.5  # 0-1 (1 = very expensive)
    feasibility_score: float = 0.5  # 0-1 (1 = very feasible)
    time_estimate: str = ""
    requirements: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class ValidationPlanResult:
    """Result from validation planning."""

    plans: list[ValidationPlan] = field(default_factory=list)
    planning_notes: str = ""
    total_plans: int = 0


class ValidationPlanningEngine:
    """Engine for designing validation plans for hypotheses."""

    def __init__(self, llm_router: LLMRouter):
        self.llm = llm_router

    async def create_validation_plan(
        self,
        hypothesis: dict[str, Any],
        idea_context: str,
    ) -> ValidationPlan:
        """Create a validation plan for a single hypothesis."""
        plan_id = str(uuid4())

        # Search for datasets
        datasets = await self._search_datasets(hypothesis, idea_context)

        # Design experiment
        experiment_design = await self._design_experiment(hypothesis, idea_context)

        # Identify baselines
        baselines = await self._identify_baselines(hypothesis, idea_context)

        # Define metrics
        metrics = await self._define_metrics(hypothesis, idea_context)

        # Define statistical tests
        statistical_tests = await self._define_statistical_tests(hypothesis, metrics)

        # Estimate cost and feasibility
        estimates = await self._estimate_cost_feasibility(
            hypothesis, datasets, experiment_design,
        )

        # Identify risks
        risks = await self._identify_risks(hypothesis, experiment_design)

        return ValidationPlan(
            id=plan_id,
            hypothesis_id=hypothesis.get("id", ""),
            dataset_candidates=datasets,
            baselines=baselines,
            metrics=metrics,
            experimental_design=experiment_design,
            statistical_tests=statistical_tests,
            difficulty_estimate=estimates.get("difficulty", 0.5),
            cost_estimate=estimates.get("cost", 0.5),
            feasibility_score=estimates.get("feasibility", 0.5),
            time_estimate=estimates.get("time_estimate", "Unknown"),
            requirements=estimates.get("requirements", []),
            risks=risks,
        )

    async def create_validation_plans(
        self,
        hypotheses: list[dict[str, Any]],
        idea_context: str,
    ) -> ValidationPlanResult:
        """Create validation plans for multiple hypotheses."""
        plans = []

        for hypothesis in hypotheses:
            try:
                plan = await self.create_validation_plan(hypothesis, idea_context)
                plans.append(plan)
            except (ValueError, RuntimeError, KeyError) as e:
                logger.error(
                    "validation_plan_error",
                    hypothesis_id=hypothesis.get("id"),
                    error=str(e),
                )
            except Exception as e:
                logger.error(
                    "validation_plan_failed",
                    hypothesis_id=hypothesis.get("id"),
                    error=str(e),
                )

        # Generate notes
        notes = await self._generate_notes(plans, hypotheses)

        return ValidationPlanResult(
            plans=plans,
            planning_notes=notes,
            total_plans=len(plans),
        )

    async def _search_datasets(
        self,
        hypothesis: dict[str, Any],
        idea_context: str,
    ) -> list[DatasetCandidate]:
        """Search for relevant datasets."""
        system = """You are a dataset discovery expert.

Find relevant datasets for testing this hypothesis.

Output a JSON object with:
- datasets: Array of dataset objects, each with:
  - name: Dataset name (string)
  - source: Where to find it (string)
  - url: URL if available (string)
  - description: Brief description (string)
  - size: Approximate size (string)
  - format: Data format (string)
  - relevance: Relevance score 0-1 (float)

Focus on publicly available, well-documented datasets."""

        user = f"""Hypothesis: {hypothesis.get('statement', '')}

IV: {hypothesis.get('independent_variable', '')}
DV: {hypothesis.get('dependent_variable', '')}

Idea context: {idea_context}

Find datasets to test this hypothesis."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        datasets = []
        for d in result.data.get("datasets", []):
            datasets.append(
                DatasetCandidate(
                    name=d.get("name", ""),
                    source=d.get("source", ""),
                    url=d.get("url"),
                    description=d.get("description", ""),
                    size=d.get("size", ""),
                    format=d.get("format", ""),
                    relevance_score=d.get("relevance", 0.5),
                ),
            )

        return datasets

    async def _design_experiment(
        self,
        hypothesis: dict[str, Any],
        idea_context: str,
    ) -> str:
        """Design an experiment to test the hypothesis."""
        system = """You are an experimental design expert.

Design a rigorous experiment to test this hypothesis.

Consider:
1. Experimental setup
2. Control conditions
3. Treatment conditions
4. Sample size requirements
5. Randomization
6. Blinding (if applicable)
7. Data collection procedure
8. Analysis plan

Provide a clear, step-by-step experimental design (300-500 words)."""

        user = f"""Hypothesis: {hypothesis.get('statement', '')}

IV: {hypothesis.get('independent_variable', '')}
DV: {hypothesis.get('dependent_variable', '')}
Baseline: {hypothesis.get('baseline', '')}
Metric: {hypothesis.get('metric', '')}
Failure condition: {hypothesis.get('failure_condition', '')}

Idea context: {idea_context}

Design an experiment to test this hypothesis."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete(messages, temperature=0.3, max_tokens=800)
        return result.content

    async def _identify_baselines(
        self,
        hypothesis: dict[str, Any],
        idea_context: str,
    ) -> list[str]:
        """Identify baselines for comparison."""
        system = """You are a research methodology expert.

Identify appropriate baselines for comparing against this hypothesis.

Output a JSON object with:
- baselines: Array of baseline descriptions (array of strings)

Consider:
1. Current state-of-the-art methods
2. Simple heuristic baselines
3. Random baselines
4. Human performance baselines
5. Previous approaches in the literature"""

        user = f"""Hypothesis: {hypothesis.get('statement', '')}

Idea context: {idea_context}

Identify baselines for comparison."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})
        return result.data.get("baselines", [])

    async def _define_metrics(
        self,
        hypothesis: dict[str, Any],
        idea_context: str,
    ) -> list[str]:
        """Define metrics for evaluation."""
        system = """You are a research evaluation expert.

Define appropriate metrics for evaluating this hypothesis.

Output a JSON object with:
- metrics: Array of metric descriptions (array of strings)

Consider:
1. Primary metrics (directly measuring the DV)
2. Secondary metrics (related measurements)
3. Efficiency metrics (time, resources)
4. Robustness metrics
5. Statistical significance measures"""

        user = f"""Hypothesis: {hypothesis.get('statement', '')}

DV: {hypothesis.get('dependent_variable', '')}
Suggested metric: {hypothesis.get('metric', '')}

Define metrics for evaluation."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})
        return result.data.get("metrics", [])

    async def _define_statistical_tests(
        self,
        hypothesis: dict[str, Any],
        metrics: list[str],
    ) -> list[str]:
        """Define appropriate statistical tests."""
        system = """You are a statistical analysis expert.

Recommend appropriate statistical tests for this hypothesis.

Output a JSON object with:
- tests: Array of test descriptions (array of strings)

Consider:
1. Parametric vs non-parametric tests
2. Multiple comparison corrections
3. Effect size measures
4. Confidence intervals
5. Power analysis requirements"""

        user = f"""Hypothesis: {hypothesis.get('statement', '')}

Metrics: {', '.join(metrics)}

Recommend statistical tests."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})
        return result.data.get("tests", [])

    async def _estimate_cost_feasibility(
        self,
        hypothesis: dict[str, Any],
        datasets: list[DatasetCandidate],
        experiment_design: str,
    ) -> dict[str, Any]:
        """Estimate cost and feasibility."""
        system = """You are a research project estimator.

Estimate the cost and feasibility of this experiment.

Output a JSON object with:
- difficulty: 0-1 (1 = very difficult)
- cost: 0-1 (1 = very expensive)
- feasibility: 0-1 (1 = very feasible)
- time_estimate: Estimated time to complete
- requirements: List of requirements (array of strings)

Consider:
1. Data availability
2. Computational requirements
3. Expertise needed
4. Time constraints
5. Resource constraints"""

        user = f"""Hypothesis: {hypothesis.get('statement', '')}

Datasets available: {len(datasets)}
Experiment design: {experiment_design[:200]}...

Estimate cost and feasibility."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})
        return result.data

    async def _identify_risks(
        self,
        hypothesis: dict[str, Any],
        experiment_design: str,
    ) -> list[str]:
        """Identify risks and mitigation strategies."""
        system = """You are a risk assessment expert.

Identify risks associated with this experiment.

Output a JSON object with:
- risks: Array of risk descriptions (array of strings)

Consider:
1. Data quality risks
2. Methodological risks
3. Resource risks
4. Timeline risks
5. Validity threats"""

        user = f"""Hypothesis: {hypothesis.get('statement', '')}

Experiment design: {experiment_design[:200]}...

Identify risks."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})
        return result.data.get("risks", [])

    async def _generate_notes(
        self,
        plans: list[ValidationPlan],
        hypotheses: list[dict[str, Any]],
    ) -> str:
        """Generate notes about validation planning."""
        if not plans:
            return "No validation plans generated."

        plans_summary = "\n".join(
            [
                f"- Hypothesis {i+1}: Feasibility={p.feasibility_score:.2f}, "
                f"Cost={p.cost_estimate:.2f}, Datasets={len(p.dataset_candidates)}"
                for i, p in enumerate(plans[:5])
            ],
        )

        system = """You are a research strategy documenter.

Given validation plans, provide brief notes on:
1. Overview of planned validations
2. Key feasibility observations
3. Resource requirements
4. Recommendations

Keep it concise (2-3 paragraphs)."""

        user = f"""Generated {len(plans)} validation plans.

Plans summary:
{plans_summary}

Provide notes on the validation plans."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete(messages, temperature=0.3, max_tokens=500)
        return result.content
