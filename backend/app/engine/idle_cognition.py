"""Idle cognition engine for autonomous background research."""

import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

import structlog

from app.llm.base import Message
from app.llm.router import LLMRouter

logger = structlog.get_logger()


@dataclass
class IdleCycleResult:
    """Result from an idle cognition cycle."""

    cycle_id: str
    idle_mode: str
    ideas_generated: int = 0
    questions_generated: int = 0
    hypotheses_generated: int = 0
    skills_created: int = 0
    papers_found: int = 0
    conflicts_found: int = 0
    duration_seconds: float = 0
    cost_usd: float = 0
    status: str = "completed"
    notes: str = ""


@dataclass
class IdleConfig:
    """Configuration for idle cognition."""

    enabled: bool = True
    trigger_minutes: int = 120
    max_cycles_per_day: int = 3
    max_minutes_per_cycle: int = 30
    max_cost_per_cycle: float = 2.0

    # Mode probabilities (must sum to 1.0)
    mode_probabilities: dict[str, float] = field(default_factory=lambda: {
        "frontier_scan": 0.35,
        "citation_conflict": 0.25,
        "revisit_rejected": 0.15,
        "cross_domain": 0.10,
        "skill_improvement": 0.10,
        "dataset_discovery": 0.05,
    })


class IdleCognitionEngine:
    """Engine for autonomous background research during idle periods."""

    def __init__(self, llm_router: LLMRouter):
        self.llm = llm_router
        self.config = IdleConfig()
        self.daily_cycles: dict[str, int] = {}  # project_id -> cycle count today

    def should_start_cycle(
        self,
        project_id: str,
        last_user_activity: datetime | None,
        active_runs: int = 0,
    ) -> bool:
        """Check if an idle cycle should start."""
        if not self.config.enabled:
            return False

        # Check if project has budget remaining
        today = datetime.now().strftime("%Y-%m-%d")
        cycle_key = f"{project_id}:{today}"
        current_cycles = self.daily_cycles.get(cycle_key, 0)

        if current_cycles >= self.config.max_cycles_per_day:
            return False

        # Check if there are active runs
        if active_runs > 0:
            return False

        # Check if user has been inactive long enough
        if last_user_activity:
            inactive_minutes = (datetime.now() - last_user_activity).total_seconds() / 60
            if inactive_minutes < self.config.trigger_minutes:
                return False

        return True

    def select_idle_mode(self) -> str:
        """Select an idle mode based on probabilities."""
        modes = list(self.config.mode_probabilities.keys())
        probabilities = list(self.config.mode_probabilities.values())
        return random.choices(modes, weights=probabilities, k=1)[0]

    async def run_idle_cycle(
        self,
        project_id: str,
        project_domain: str,
        recent_papers: list[dict[str, Any]] | None = None,
        rejected_ideas: list[dict[str, Any]] | None = None,
    ) -> IdleCycleResult:
        """Run a single idle cognition cycle."""
        cycle_id = str(uuid4())
        start_time = datetime.now()

        # Increment cycle count
        today = datetime.now().strftime("%Y-%m-%d")
        cycle_key = f"{project_id}:{today}"
        self.daily_cycles[cycle_key] = self.daily_cycles.get(cycle_key, 0) + 1

        # Select mode
        mode = self.select_idle_mode()

        logger.info(
            "idle_cycle_started",
            cycle_id=cycle_id,
            project_id=project_id,
            mode=mode,
        )

        try:
            if mode == "frontier_scan":
                result = await self._run_frontier_scan(cycle_id, project_id, project_domain)
            elif mode == "citation_conflict":
                result = await self._run_citation_conflict(cycle_id, project_id, project_domain)
            elif mode == "revisit_rejected":
                result = await self._run_revisit_rejected(cycle_id, project_id, rejected_ideas)
            elif mode == "cross_domain":
                result = await self._run_cross_domain(cycle_id, project_id, project_domain)
            elif mode == "skill_improvement":
                result = await self._run_skill_improvement(cycle_id, project_id)
            elif mode == "dataset_discovery":
                result = await self._run_dataset_discovery(cycle_id, project_id, project_domain)
            else:
                result = IdleCycleResult(
                    cycle_id=cycle_id,
                    idle_mode=mode,
                    status="failed",
                    notes=f"Unknown mode: {mode}",
                )

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            result.duration_seconds = duration

            logger.info(
                "idle_cycle_completed",
                cycle_id=cycle_id,
                mode=mode,
                duration=duration,
                ideas=result.ideas_generated,
                questions=result.questions_generated,
            )

            return result

        except asyncio.CancelledError:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error("idle_cycle_failed", cycle_id=cycle_id, error=str(e))
            return IdleCycleResult(
                cycle_id=cycle_id,
                idle_mode=mode,
                status="failed",
                notes=str(e),
                duration_seconds=(datetime.now() - start_time).total_seconds(),
            )

    async def _run_frontier_scan(
        self,
        cycle_id: str,
        project_id: str,
        domain: str,
    ) -> IdleCycleResult:
        """Run a frontier literature scan."""
        system = """You are a scientific frontier scanner.

Scan for recent developments and frontier papers in this domain.

Output a JSON object with:
- findings: Key recent developments (array of strings)
- new_directions: Emerging research directions (array of strings)
- notable_papers: Notable recent papers (array of objects with title, year, key_contribution)
- opportunities: Research opportunities identified (array of strings)
- summary: Brief summary of frontier status (string)"""

        user = f"""Domain: {domain}

Scan for recent frontier developments and identify research opportunities."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        return IdleCycleResult(
            cycle_id=cycle_id,
            idle_mode="frontier_scan",
            papers_found=len(result.data.get("notable_papers", [])),
            notes=result.data.get("summary", ""),
        )

    async def _run_citation_conflict(
        self,
        cycle_id: str,
        project_id: str,
        domain: str,
    ) -> IdleCycleResult:
        """Run a citation-conflict question generation cycle."""
        system = """You are a scientific conflict detector.

Identify citation conflicts and generate research questions.

Output a JSON object with:
- conflicts: Identified conflicts (array of objects with description, papers, severity)
- questions: Generated research questions (array of strings)
- hypotheses: Candidate hypotheses (array of strings)
- summary: Brief summary (string)"""

        user = f"""Domain: {domain}

Detect citation conflicts and generate research questions."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        return IdleCycleResult(
            cycle_id=cycle_id,
            idle_mode="citation_conflict",
            questions_generated=len(result.data.get("questions", [])),
            hypotheses_generated=len(result.data.get("hypotheses", [])),
            conflicts_found=len(result.data.get("conflicts", [])),
            notes=result.data.get("summary", ""),
        )

    async def _run_revisit_rejected(
        self,
        cycle_id: str,
        project_id: str,
        rejected_ideas: list[dict[str, Any]] | None,
    ) -> IdleCycleResult:
        """Run a rejected idea revisit cycle."""
        if not rejected_ideas:
            return IdleCycleResult(
                cycle_id=cycle_id,
                idle_mode="revisit_rejected",
                notes="No rejected ideas to revisit",
            )

        ideas_summary = "\n".join(
            [
                f"- {idea.get('text', '')[:100]}... (reason: {idea.get('rejection_reason', 'N/A')})"
                for idea in rejected_ideas[:5]
            ],
        )

        system = """You are a research idea revisitor.

Revisit rejected ideas with fresh perspective.

Output a JSON object with:
- revived_ideas: Ideas that deserve reconsideration (array of strings)
- new_angles: New angles to explore (array of strings)
- updated_assessment: Updated assessment of rejected ideas (string)
- summary: Brief summary (string)"""

        user = f"""Rejected ideas to revisit:
{ideas_summary}

Are any of these worth reconsidering with new perspectives?"""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        return IdleCycleResult(
            cycle_id=cycle_id,
            idle_mode="revisit_rejected",
            ideas_generated=len(result.data.get("revived_ideas", [])),
            notes=result.data.get("summary", ""),
        )

    async def _run_cross_domain(
        self,
        cycle_id: str,
        project_id: str,
        domain: str,
    ) -> IdleCycleResult:
        """Run a cross-domain collision cycle."""
        system = """You are a cross-domain innovation expert.

Generate novel ideas by combining concepts from different domains.

Output a JSON object with:
- collisions: Cross-domain idea collisions (array of objects with domain1, domain2, idea, novelty_score)
- transferable_mechanisms: Mechanisms that could transfer (array of strings)
- novel_hypotheses: Novel hypotheses from collisions (array of strings)
- summary: Brief summary (string)"""

        user = f"""Primary domain: {domain}

Generate cross-domain collisions that could lead to novel research ideas."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        return IdleCycleResult(
            cycle_id=cycle_id,
            idle_mode="cross_domain",
            ideas_generated=len(result.data.get("collisions", [])),
            notes=result.data.get("summary", ""),
        )

    async def _run_skill_improvement(
        self,
        cycle_id: str,
        project_id: str,
    ) -> IdleCycleResult:
        """Run a skill improvement cycle."""
        system = """You are a research skill optimizer.

Identify opportunities to improve research skills.

Output a JSON object with:
- skill_gaps: Identified skill gaps (array of strings)
- improvement_suggestions: Suggestions for existing skills (array of strings)
- new_skills_needed: New skills that should be created (array of strings)
- summary: Brief summary (string)"""

        user = """Analyze research processes and identify skill improvement opportunities."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        return IdleCycleResult(
            cycle_id=cycle_id,
            idle_mode="skill_improvement",
            skills_created=len(result.data.get("new_skills_needed", [])),
            notes=result.data.get("summary", ""),
        )

    async def _run_dataset_discovery(
        self,
        cycle_id: str,
        project_id: str,
        domain: str,
    ) -> IdleCycleResult:
        """Run a dataset discovery cycle."""
        system = """You are a dataset discovery expert.

Find relevant datasets for research in this domain.

Output a JSON object with:
- datasets: Discovered datasets (array of objects with name, source, description, relevance)
- benchmarks: Benchmark datasets (array of strings)
- data_gaps: Missing datasets that would be valuable (array of strings)
- summary: Brief summary (string)"""

        user = f"""Domain: {domain}

Discover relevant datasets and benchmarks for research."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        return IdleCycleResult(
            cycle_id=cycle_id,
            idle_mode="dataset_discovery",
            papers_found=len(result.data.get("datasets", [])),
            notes=result.data.get("summary", ""),
        )

    def get_daily_stats(self, project_id: str) -> dict[str, Any]:
        """Get daily cycle statistics for a project."""
        today = datetime.now().strftime("%Y-%m-%d")
        cycle_key = f"{project_id}:{today}"

        return {
            "cycles_today": self.daily_cycles.get(cycle_key, 0),
            "max_cycles_per_day": self.config.max_cycles_per_day,
            "remaining_cycles": max(0, self.config.max_cycles_per_day - self.daily_cycles.get(cycle_key, 0)),
        }
