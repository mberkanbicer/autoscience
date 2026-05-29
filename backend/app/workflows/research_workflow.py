"""Durable workflow engine for coordinating research agents."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Awaitable
from enum import Enum
from uuid import uuid4

import structlog

from ..schemas.research_state import ResearchState, RunState, RunBudget
from ..agents.base import AgentRole, BaseAgent, AgentInput, AgentOutput

logger = structlog.get_logger()


class WorkflowStep(str, Enum):
    """Steps in the research workflow."""

    INITIALIZE = "initialize"
    INTERPRET_INTENT = "interpret_intent"
    PLAN_SEARCH = "plan_search"
    RETRIEVE_LITERATURE = "retrieve_literature"
    ANALYZE_PAPERS = "analyze_papers"
    CLUSTER_PAPERS = "cluster_papers"
    DETECT_CONFLICTS = "detect_conflicts"
    GENERATE_QUESTIONS = "generate_questions"
    FORM_HYPOTHESES = "form_hypotheses"
    PLAN_VALIDATION = "plan_validation"
    SCORE_IDEA = "score_idea"
    MAKE_DECISION = "make_decision"
    CREATE_SKILLS = "create_skills"
    GENERATE_REPORT = "generate_report"
    COMPLETE = "complete"


class WorkflowStatus(str, Enum):
    """Status of a workflow."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStepResult:
    """Result from a workflow step."""

    step: WorkflowStep
    status: str  # completed, failed, skipped
    output: dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0
    error: str | None = None


@dataclass
class WorkflowConfig:
    """Configuration for a workflow."""

    run_type: str  # user_directed, flexible_user, idle_autonomous
    flexibility: float = 0.6
    max_steps: int = 15
    enable_skeptic: bool = True
    enable_skill_creation: bool = True
    approval_required: list[str] = field(default_factory=list)


class ResearchWorkflow:
    """Durable workflow for coordinating research agents."""

    def __init__(
        self,
        agents: dict[AgentRole, BaseAgent],
        config: WorkflowConfig | None = None,
    ):
        self.agents = agents
        self.config = config or WorkflowConfig(run_type="user_directed")
        self.step_history: list[WorkflowStepResult] = []
        self.status = WorkflowStatus.PENDING

    async def run(self, state: ResearchState) -> ResearchState:
        """Run the complete research workflow."""
        self.status = WorkflowStatus.RUNNING
        state.state = RunState.RUNNING
        state.started_at = datetime.utcnow()

        logger.info(
            "workflow_started",
            run_id=state.run_id,
            run_type=self.config.run_type,
        )

        try:
            # Execute workflow steps based on run type
            if self.config.run_type == "user_directed":
                state = await self._run_user_directed(state)
            elif self.config.run_type == "flexible_user":
                state = await self._run_flexible_user(state)
            elif self.config.run_type == "idle_autonomous":
                state = await self._run_idle_autonomous(state)
            else:
                raise ValueError(f"Unknown run type: {self.config.run_type}")

            # Complete workflow
            self.status = WorkflowStatus.COMPLETED
            state.state = RunState.COMPLETED
            state.completed_at = datetime.utcnow()
            state.current_phase = "completed"

        except Exception as e:
            logger.error("workflow_failed", error=str(e))
            self.status = WorkflowStatus.FAILED
            state.state = RunState.FAILED
            state.add_error("workflow_failed", str(e))

        return state

    async def _run_user_directed(self, state: ResearchState) -> ResearchState:
        """Run user-directed research workflow."""
        # Step 1: Interpret intent
        state = await self._execute_step(
            state, WorkflowStep.INTERPRET_INTENT, self._interpret_intent
        )

        # Step 2: Plan search
        state = await self._execute_step(
            state, WorkflowStep.PLAN_SEARCH, self._plan_search
        )

        # Step 3: Retrieve literature
        state = await self._execute_step(
            state, WorkflowStep.RETRIEVE_LITERATURE, self._retrieve_literature
        )

        # Step 4: Analyze papers
        state = await self._execute_step(
            state, WorkflowStep.ANALYZE_PAPERS, self._analyze_papers
        )

        # Step 5: Cluster papers
        state = await self._execute_step(
            state, WorkflowStep.CLUSTER_PAPERS, self._cluster_papers
        )

        # Step 6: Detect conflicts
        state = await self._execute_step(
            state, WorkflowStep.DETECT_CONFLICTS, self._detect_conflicts
        )

        # Step 7: Generate questions
        state = await self._execute_step(
            state, WorkflowStep.GENERATE_QUESTIONS, self._generate_questions
        )

        # Step 8: Form hypotheses
        state = await self._execute_step(
            state, WorkflowStep.FORM_HYPOTHESES, self._form_hypotheses
        )

        # Step 9: Plan validation
        state = await self._execute_step(
            state, WorkflowStep.PLAN_VALIDATION, self._plan_validation
        )

        # Step 10: Score idea
        state = await self._execute_step(
            state, WorkflowStep.SCORE_IDEA, self._score_idea
        )

        # Step 11: Make decision
        state = await self._execute_step(
            state, WorkflowStep.MAKE_DECISION, self._make_decision
        )

        # Step 12: Create skills (if enabled)
        if self.config.enable_skill_creation:
            state = await self._execute_step(
                state, WorkflowStep.CREATE_SKILLS, self._create_skills
            )

        # Step 13: Generate report
        state = await self._execute_step(
            state, WorkflowStep.GENERATE_REPORT, self._generate_report
        )

        return state

    async def _run_flexible_user(self, state: ResearchState) -> ResearchState:
        """Run flexible user research workflow."""
        # Same as user-directed but with more flexibility
        return await self._run_user_directed(state)

    async def _run_idle_autonomous(self, state: ResearchState) -> ResearchState:
        """Run autonomous idle research workflow."""
        # Simplified workflow for idle cycles
        state = await self._execute_step(
            state, WorkflowStep.RETRIEVE_LITERATURE, self._retrieve_literature
        )

        state = await self._execute_step(
            state, WorkflowStep.DETECT_CONFLICTS, self._detect_conflicts
        )

        state = await self._execute_step(
            state, WorkflowStep.GENERATE_QUESTIONS, self._generate_questions
        )

        state = await self._execute_step(
            state, WorkflowStep.SCORE_IDEA, self._score_idea
        )

        return state

    async def _execute_step(
        self,
        state: ResearchState,
        step: WorkflowStep,
        handler: Callable[[ResearchState], Awaitable[ResearchState]],
    ) -> ResearchState:
        """Execute a single workflow step."""
        start_time = datetime.now()
        state.current_phase = step.value
        state.add_event("step_started", details={"step": step.value})

        try:
            # Check budget
            if state.is_budget_exceeded():
                logger.warning("budget_exceeded", run_id=state.run_id)
                state.add_event("budget_exceeded")
                return state

            # Execute handler
            state = await handler(state)

            # Record success
            duration = (datetime.now() - start_time).total_seconds()
            result = WorkflowStepResult(
                step=step,
                status="completed",
                duration_seconds=duration,
            )
            self.step_history.append(result)

            state.add_event(
                "step_completed",
                details={"step": step.value, "duration": duration},
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            result = WorkflowStepResult(
                step=step,
                status="failed",
                duration_seconds=duration,
                error=str(e),
            )
            self.step_history.append(result)

            state.add_error(f"step_failed_{step.value}", str(e))
            logger.error("step_failed", step=step.value, error=str(e))

        return state

    # Step Handlers

    async def _interpret_intent(self, state: ResearchState) -> ResearchState:
        """Interpret user intent."""
        agent = self.agents.get(AgentRole.USER_INTENT)
        if not agent:
            return state

        input = AgentInput(
            task=f"Interpret this research idea: {state.original_idea}",
            context={"flexibility": state.flexibility},
        )

        output = await agent.run(input)
        state.current_phase = "intent_interpreted"
        return state

    async def _plan_search(self, state: ResearchState) -> ResearchState:
        """Plan literature search."""
        state.current_phase = "search_planned"
        return state

    async def _retrieve_literature(self, state: ResearchState) -> ResearchState:
        """Retrieve literature."""
        agent = self.agents.get(AgentRole.LITERATURE)
        if not agent:
            return state

        input = AgentInput(
            task=f"Search for papers related to: {state.current_idea}",
            context={"max_sources": state.budget.max_sources},
        )

        output = await agent.run(input)
        state.sources_searched += 10  # Simulated
        state.current_phase = "literature_retrieved"
        return state

    async def _analyze_papers(self, state: ResearchState) -> ResearchState:
        """Analyze papers."""
        agent = self.agents.get(AgentRole.PAPER_ANALYST)
        if not agent:
            return state

        input = AgentInput(
            task="Analyze retrieved papers",
            context={"papers": [p.model_dump() for p in state.papers[:5]]},
        )

        output = await agent.run(input)
        state.current_phase = "papers_analyzed"
        return state

    async def _cluster_papers(self, state: ResearchState) -> ResearchState:
        """Cluster papers."""
        agent = self.agents.get(AgentRole.CLUSTER)
        if not agent:
            return state

        input = AgentInput(
            task="Cluster papers by theme",
            context={"papers": [p.model_dump() for p in state.papers[:10]]},
        )

        output = await agent.run(input)
        state.current_phase = "papers_clustered"
        return state

    async def _detect_conflicts(self, state: ResearchState) -> ResearchState:
        """Detect conflicts."""
        agent = self.agents.get(AgentRole.CONFLICT)
        if not agent:
            return state

        input = AgentInput(
            task="Detect conflicts in the literature",
            context={"papers": [p.model_dump() for p in state.papers[:10]]},
        )

        output = await agent.run(input)
        state.current_phase = "conflicts_detected"
        return state

    async def _generate_questions(self, state: ResearchState) -> ResearchState:
        """Generate research questions."""
        agent = self.agents.get(AgentRole.RESEARCH_QUESTION)
        if not agent:
            return state

        input = AgentInput(
            task="Generate research questions from conflicts",
            context={
                "idea": state.current_idea,
                "conflicts": [c.model_dump() for c in state.conflicts],
            },
        )

        output = await agent.run(input)
        state.current_phase = "questions_generated"
        return state

    async def _form_hypotheses(self, state: ResearchState) -> ResearchState:
        """Form hypotheses."""
        agent = self.agents.get(AgentRole.HYPOTHESIS)
        if not agent:
            return state

        input = AgentInput(
            task="Form testable hypotheses from questions",
            context={
                "idea": state.current_idea,
                "questions": [q.model_dump() for q in state.questions],
            },
        )

        output = await agent.run(input)
        state.current_phase = "hypotheses_formed"
        return state

    async def _plan_validation(self, state: ResearchState) -> ResearchState:
        """Plan validation."""
        agent = self.agents.get(AgentRole.VALIDATION_PLANNER)
        if not agent:
            return state

        input = AgentInput(
            task="Design validation plan for hypotheses",
            context={
                "hypotheses": [h.model_dump() for h in state.hypotheses],
            },
        )

        output = await agent.run(input)
        state.current_phase = "validation_planned"
        return state

    async def _score_idea(self, state: ResearchState) -> ResearchState:
        """Score the idea."""
        # Use scoring engine directly
        state.current_phase = "idea_scored"
        return state

    async def _make_decision(self, state: ResearchState) -> ResearchState:
        """Make decision on next action."""
        agent = self.agents.get(AgentRole.DECISION)
        if not agent:
            return state

        input = AgentInput(
            task="Decide next action based on research progress",
            context={
                "idea": state.current_idea,
                "phase": state.current_phase,
                "papers_found": len(state.papers),
                "conflicts_found": len(state.conflicts),
                "questions_found": len(state.questions),
            },
        )

        output = await agent.run(input)
        state.current_phase = "decision_made"
        return state

    async def _create_skills(self, state: ResearchState) -> ResearchState:
        """Create skills from successful patterns."""
        agent = self.agents.get(AgentRole.SKILL_CURATOR)
        if not agent:
            return state

        input = AgentInput(
            task="Identify and create reusable research skills",
            context={"workflow_steps": [s.step.value for s in self.step_history]},
        )

        output = await agent.run(input)
        state.current_phase = "skills_created"
        return state

    async def _generate_report(self, state: ResearchState) -> ResearchState:
        """Generate research report."""
        agent = self.agents.get(AgentRole.ARCHIVIST)
        if not agent:
            return state

        input = AgentInput(
            task="Generate comprehensive research report",
            context={
                "idea": state.current_idea,
                "papers": len(state.papers),
                "conflicts": len(state.conflicts),
                "questions": len(state.questions),
                "hypotheses": len(state.hypotheses),
            },
        )

        output = await agent.run(input)
        state.current_phase = "report_generated"
        return state

    def pause(self) -> None:
        """Pause the workflow."""
        self.status = WorkflowStatus.PAUSED

    def resume(self) -> None:
        """Resume the workflow."""
        self.status = WorkflowStatus.RUNNING

    def cancel(self) -> None:
        """Cancel the workflow."""
        self.status = WorkflowStatus.CANCELLED

    def get_step_history(self) -> list[WorkflowStepResult]:
        """Get the step history."""
        return self.step_history

    def get_total_duration(self) -> float:
        """Get total workflow duration."""
        return sum(s.duration_seconds for s in self.step_history)
