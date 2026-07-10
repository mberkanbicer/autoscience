"""Durable workflow engine for coordinating research agents."""

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

import structlog

from app.agents.base import AgentInput, AgentRole, BaseAgent
from app.engine.claims_pipeline import extract_claims
from app.schemas.research_run import ResearchRunUpdate
from app.schemas.research_state import ResearchState, RunState

from .safety_gates import (
    GATED_STEPS,
    STEP_COST_ESTIMATES,
    ApprovalGateError,
    ProjectSafetySettings,
    enforce_step_safety_gate,
)

logger = structlog.get_logger()

_CODE_BLOCK_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def _extract_python_code(text: str) -> str | None:
    """Pull Python from fenced code blocks in LLM output."""
    match = _CODE_BLOCK_RE.search(text)
    if match:
        return match.group(1).strip()
    stripped = text.strip()
    if stripped.startswith("import ") or stripped.startswith("def ") or stripped.startswith("print("):
        return stripped
    return None


def _fallback_experiment_code(hypothesis_statement: str) -> str:
    """Minimal deterministic script when codegen is unavailable."""
    safe_stmt = hypothesis_statement.replace('"', "'")[:200]
    return (
        "import json\n"
        f'print("Validating hypothesis: {safe_stmt}")\n'
        'result = {"status": "completed", "note": "synthetic validation scaffold"}\n'
        "print(json.dumps(result))\n"
    )


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
    GENERATE_EXPERIMENT = "generate_experiment"
    RUN_EXPERIMENT = "run_experiment"
    VALIDATE_HYPOTHESES = "validate_hypotheses"
    CREATE_SKILLS = "create_skills"
    GENERATE_MANUSCRIPT = "generate_manuscript"
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


def serialize_step_history(step_history: list["WorkflowStepResult"]) -> list[dict[str, Any]]:
    """Convert in-memory step history to JSON-serializable records."""
    return [
        {
            "step": result.step.value,
            "status": result.status,
            "duration_seconds": result.duration_seconds,
            "error": result.error,
            "output": result.output,
        }
        for result in step_history
    ]


def deserialize_step_history(records: list[dict[str, Any]]) -> list["WorkflowStepResult"]:
    """Restore in-memory step history from persisted JSON records."""
    restored: list[WorkflowStepResult] = []
    for record in records:
        step_value = record.get("step")
        if not step_value:
            continue
        try:
            step = WorkflowStep(step_value)
        except ValueError:
            continue
        restored.append(
            WorkflowStepResult(
                step=step,
                status=record.get("status", "completed"),
                duration_seconds=float(record.get("duration_seconds") or 0),
                error=record.get("error"),
                output=record.get("output") or {},
            ),
        )
    return restored


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
        run_id: str | None = None,
        run_service=None,
        keyword_engine=None,
        literature_engine=None,
        analysis_engine=None,
        clustering_engine=None,
        conflict_engine=None,
        question_engine=None,
        hypothesis_engine=None,
        validation_engine=None,
        scoring_engine=None,
        idea_ledger=None,
        db=None,
        event_broadcaster=None,
        safety_service=None,
        project_safety_settings: ProjectSafetySettings | None = None,
        knowledge_service=None,
    ):
        self.agents = agents
        self.config = config or WorkflowConfig(run_type="user_directed")
        self.step_history: list[WorkflowStepResult] = []
        self.status = WorkflowStatus.PENDING
        self.run_id = run_id
        self.run_service = run_service
        self.safety_service = safety_service
        self.project_safety_settings = project_safety_settings or ProjectSafetySettings()
        self.keyword_engine = keyword_engine
        self.literature_engine = literature_engine
        self.analysis_engine = analysis_engine
        self.clustering_engine = clustering_engine
        self.conflict_engine = conflict_engine
        self.question_engine = question_engine
        self.hypothesis_engine = hypothesis_engine
        self.validation_engine = validation_engine
        self.scoring_engine = scoring_engine
        self.idea_ledger = idea_ledger
        self.db = db
        self.event_broadcaster = event_broadcaster
        self.knowledge_service = knowledge_service

    @property
    def _knowledge(self):
        """Return injected knowledge service, with lazy fallback for tests."""
        if self.knowledge_service is None and self.db is not None:
            from app.services.knowledge_service import KnowledgeBaseService
            self.knowledge_service = KnowledgeBaseService(self.db)
        return self.knowledge_service

    def _is_flexible_mode(self) -> bool:
        return self.config.run_type == "flexible_user"

    def _literature_limit(self, state: ResearchState) -> int:
        base = min(state.budget.max_sources, 30)
        if self._is_flexible_mode():
            return min(state.budget.max_sources, base + int(state.flexibility * 30))
        return base

    def _literature_year_span(self) -> int:
        return 10 if self._is_flexible_mode() else 5

    async def _generate_wiki_notes(self, state: ResearchState) -> None:
        """Auto-generate wiki notes from research results."""
        if not self._knowledge:
            return
        try:
            # Paper notes (up to 10)
            for p in state.papers[:10]:
                try:
                    content = await self._knowledge.generate_paper_note(
                        paper_id=p.id,
                        paper_data={"title": p.title, "authors": p.authors, "year": p.year},
                    )
                    await self._knowledge.upsert_note(
                        project_id=state.project_id,
                        note_type="paper",
                        title=f"Paper: {p.title[:200]}",
                        content=content,
                        entity_id=p.id,
                        run_id=state.run_id,
                    )
                except Exception as e:
                    logger.debug("wiki_paper_note_failed", paper=p.title[:50], error=str(e))

            # Cluster notes
            for c in state.clusters:
                try:
                    content = await self._knowledge.generate_cluster_note({
                        "name": c.name,
                        "description": c.description,
                        "paper_count": c.paper_count,
                    })
                    await self._knowledge.upsert_note(
                        project_id=state.project_id,
                        note_type="cluster",
                        title=f"Cluster: {c.name[:200]}",
                        content=content,
                        entity_id=c.id,
                        run_id=state.run_id,
                    )
                except Exception as e:
                    logger.debug("wiki_cluster_note_failed", cluster=c.name[:50], error=str(e))

            # Conflict notes
            for c in state.conflicts:
                try:
                    content = await self._knowledge.generate_conflict_note({
                        "conflict_type": c.conflict_type,
                        "description": c.description,
                        "severity": c.severity,
                    })
                    await self._knowledge.upsert_note(
                        project_id=state.project_id,
                        note_type="conflict",
                        title=f"Conflict: {c.conflict_type[:200]}",
                        content=content,
                        entity_id=c.id,
                        run_id=state.run_id,
                    )
                except Exception as e:
                    logger.debug("wiki_conflict_note_failed", conflict=c.conflict_type[:50], error=str(e))

            # Hypothesis notes (up to 5)
            for h in state.hypotheses[:5]:
                try:
                    content = await self._knowledge.generate_hypothesis_note({
                        "statement": h.statement,
                        "confidence": h.confidence,
                        "status": h.status,
                    })
                    await self._knowledge.upsert_note(
                        project_id=state.project_id,
                        note_type="hypothesis",
                        title=f"Hypothesis: {h.statement[:200]}",
                        content=content,
                        entity_id=h.id,
                        run_id=state.run_id,
                    )
                except Exception as e:
                    logger.debug("wiki_hypothesis_note_failed", hypothesis=h.statement[:50], error=str(e))

            await self.db.flush()
            logger.info("wiki_notes_generated",
                        project=state.project_id,
                        papers=len(state.papers),
                        clusters=len(state.clusters),
                        conflicts=len(state.conflicts),
                        hypotheses=len(state.hypotheses))
        except Exception as e:
            logger.warning("wiki_note_generation_failed", error=str(e), exc_info=True)

    async def run(self, state: ResearchState) -> ResearchState:
        """Run the complete research workflow."""
        self.status = WorkflowStatus.RUNNING
        state.state = RunState.RUNNING
        state.started_at = datetime.now(UTC)

        logger.info(
            "workflow_started",
            run_id=state.run_id,
            run_type=self.config.run_type,
        )

        # Load relevant skills into state at the start of the workflow
        try:
            if self.db and state.project_id:
                from app.services.skill_memory_service import SkillMemoryService
                sms = SkillMemoryService(self.db)
                relevant = await sms.get_relevant_skills(
                    context=state.current_idea,
                    limit=5,
                )
                state.skills_used = [s.id for s in relevant]
                if relevant:
                    logger.info(
                        "skills_loaded",
                        count=len(relevant),
                        skill_names=[s.name for s in relevant],
                    )
                    await self._broadcast_event(
                        "skills_loaded",
                        details={
                            "count": len(relevant),
                            "skill_names": [s.name for s in relevant],
                        },
                    )
        except Exception as e:
            logger.warning("skill_retrieval_failed", error=str(e), exc_info=True)

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
            state.completed_at = datetime.now(UTC)
            state.current_phase = "completed"

            # Broadcast completion
            await self._broadcast_event(
                "run_completed",
                details={
                    "papers": len(state.papers),
                    "conflicts": len(state.conflicts),
                    "questions": len(state.questions),
                    "hypotheses": len(state.hypotheses),
                },
            )

        except ApprovalGateError as gate_error:
            self.status = WorkflowStatus.WAITING_APPROVAL
            state.state = RunState.WAITING_FOR_APPROVAL
            state.add_error("approval_required", gate_error.message)
            await self._broadcast_event(
                "approval_required",
                details={
                    "approval_id": gate_error.approval_id,
                    "step": gate_error.step,
                    "message": gate_error.message,
                },
            )
            raise
        except Exception as e:
            logger.error("workflow_failed", error=str(e), exc_info=True)
            self.status = WorkflowStatus.FAILED
            state.state = RunState.FAILED
            state.add_error("workflow_failed", str(e))

            # Broadcast failure
            await self._broadcast_event(
                "run_failed",
                details={"error": str(e)},
            )

        return state

    async def run_from_step(
        self,
        state: ResearchState,
        start_step: WorkflowStep,
    ) -> ResearchState:
        """Resume a workflow from a specific step (after approval)."""
        self.status = WorkflowStatus.RUNNING
        state.state = RunState.RUNNING

        if self.config.run_type in ("user_directed", "flexible_user"):
            state = await self._run_user_directed(state, from_step=start_step)
        elif self.config.run_type == "idle_autonomous":
            state = await self._run_idle_autonomous(state)
        else:
            raise ValueError(f"Unknown run type: {self.config.run_type}")

        if self.status not in (WorkflowStatus.WAITING_APPROVAL, WorkflowStatus.FAILED):
            self.status = WorkflowStatus.COMPLETED
            state.state = RunState.COMPLETED
            state.completed_at = datetime.now(UTC)
            state.current_phase = "completed"
            await self._broadcast_event(
                "run_completed",
                details={
                    "papers": len(state.papers),
                    "conflicts": len(state.conflicts),
                    "questions": len(state.questions),
                    "hypotheses": len(state.hypotheses),
                },
            )

        return state

    async def _run_user_directed(
        self,
        state: ResearchState,
        from_step: WorkflowStep | None = None,
    ) -> ResearchState:
        """Run user-directed research workflow, optionally resuming from a step."""
        executing = from_step is None

        def should_run(step: WorkflowStep) -> bool:
            nonlocal executing
            if executing:
                return True
            if step == from_step:
                executing = True
                return True
            return False

        if should_run(WorkflowStep.INTERPRET_INTENT):
            state = await self._execute_step(
                state, WorkflowStep.INTERPRET_INTENT, self._interpret_intent, required=True,
            )
        if should_run(WorkflowStep.PLAN_SEARCH):
            state = await self._execute_step(
                state, WorkflowStep.PLAN_SEARCH, self._plan_search, required=True,
            )
        if should_run(WorkflowStep.RETRIEVE_LITERATURE):
            state = await self._execute_step(
                state, WorkflowStep.RETRIEVE_LITERATURE, self._retrieve_literature, required=True,
            )
        if should_run(WorkflowStep.ANALYZE_PAPERS):
            state = await self._execute_step(
                state, WorkflowStep.ANALYZE_PAPERS, self._analyze_papers,
            )
        if should_run(WorkflowStep.CLUSTER_PAPERS):
            state = await self._execute_step(
                state, WorkflowStep.CLUSTER_PAPERS, self._cluster_papers,
            )
        if should_run(WorkflowStep.DETECT_CONFLICTS):
            state = await self._execute_step(
                state, WorkflowStep.DETECT_CONFLICTS, self._detect_conflicts,
            )
        if should_run(WorkflowStep.GENERATE_QUESTIONS):
            state = await self._execute_step(
                state, WorkflowStep.GENERATE_QUESTIONS, self._generate_questions,
            )
        if should_run(WorkflowStep.FORM_HYPOTHESES):
            state = await self._execute_step(
                state, WorkflowStep.FORM_HYPOTHESES, self._form_hypotheses,
            )
        if should_run(WorkflowStep.PLAN_VALIDATION):
            state = await self._execute_step(
                state, WorkflowStep.PLAN_VALIDATION, self._plan_validation,
            )
        if should_run(WorkflowStep.SCORE_IDEA):
            state = await self._execute_step(
                state, WorkflowStep.SCORE_IDEA, self._score_idea,
            )
        if should_run(WorkflowStep.MAKE_DECISION):
            state = await self._execute_step(
                state, WorkflowStep.MAKE_DECISION, self._make_decision,
            )
        if should_run(WorkflowStep.GENERATE_EXPERIMENT):
            state = await self._execute_step(
                state, WorkflowStep.GENERATE_EXPERIMENT, self._generate_experiment,
            )
        if should_run(WorkflowStep.RUN_EXPERIMENT):
            state = await self._execute_step(
                state, WorkflowStep.RUN_EXPERIMENT, self._run_experiment,
            )
        if should_run(WorkflowStep.VALIDATE_HYPOTHESES):
            state = await self._execute_step(
                state, WorkflowStep.VALIDATE_HYPOTHESES, self._validate_hypotheses,
            )
        if self.config.enable_skill_creation and should_run(WorkflowStep.CREATE_SKILLS):
            state = await self._execute_step(
                state, WorkflowStep.CREATE_SKILLS, self._create_skills,
            )

        if executing:
            await self._generate_wiki_notes(state)

        if should_run(WorkflowStep.GENERATE_MANUSCRIPT):
            state = await self._execute_step(
                state, WorkflowStep.GENERATE_MANUSCRIPT, self._generate_manuscript,
            )
        if should_run(WorkflowStep.GENERATE_REPORT):
            state = await self._execute_step(
                state, WorkflowStep.GENERATE_REPORT, self._generate_report,
            )

        return state

    async def _run_flexible_user(self, state: ResearchState) -> ResearchState:
        """Run flexible user research workflow with broader exploration."""
        state.flexibility = max(state.flexibility, 0.75)
        state.budget.max_sources = min(state.budget.max_sources + 20, 80)
        self.config.enable_skill_creation = True
        return await self._run_user_directed(state)

    async def _run_idle_autonomous(self, state: ResearchState) -> ResearchState:
        """Run autonomous idle research workflow."""
        # Simplified workflow for idle cycles
        state = await self._execute_step(
            state, WorkflowStep.RETRIEVE_LITERATURE, self._retrieve_literature,
        )

        state = await self._execute_step(
            state, WorkflowStep.DETECT_CONFLICTS, self._detect_conflicts,
        )

        state = await self._execute_step(
            state, WorkflowStep.GENERATE_QUESTIONS, self._generate_questions,
        )

        state = await self._execute_step(
            state, WorkflowStep.SCORE_IDEA, self._score_idea,
        )

        # Generate wiki notes
        await self._generate_wiki_notes(state)

        return state

    async def _execute_step(
        self,
        state: ResearchState,
        step: WorkflowStep,
        handler: Callable[[ResearchState], Awaitable[ResearchState]],
        required: bool = False,
    ) -> ResearchState:
        """Execute a single workflow step."""
        start_time = datetime.now()
        state.current_phase = step.value
        state.add_event("step_started", details={"step": step.value})

        # Hard budget-cap check: if the run has exhausted its budget and is NOT
        # already in a budget-extension-approval flow, raise ApprovalGateError
        # so the user can approve a budget extension or terminate.
        if state.is_budget_exceeded() and not state.budget_extension_approved:
            budget_remaining = state.budget_remaining()
            gate_message = (
                f"Run budget exhausted: "
                f"${state.cost_usd:.2f} / ${state.budget.max_cost_usd:.2f} spent, "
                f"{state.minutes_elapsed:.0f}/{state.budget.max_minutes} min, "
                f"{state.sources_searched}/{state.budget.max_sources} sources. "
                f"Approve a budget extension to continue, or terminate the run."
            )
            logger.warning("budget_exceeded", run_id=state.run_id, **budget_remaining)
            await self._broadcast_event(
                "budget_exceeded",
                details={
                    "cost_usd": state.cost_usd,
                    "max_cost_usd": state.budget.max_cost_usd,
                    "minutes_elapsed": state.minutes_elapsed,
                    "max_minutes": state.budget.max_minutes,
                    "sources_searched": state.sources_searched,
                    "max_sources": state.budget.max_sources,
                    "budget_remaining": budget_remaining,
                },
            )
            if self.safety_service:
                approval = await self.safety_service.request_approval(
                    project_id=state.project_id,
                    run_id=self.run_id,
                    action_type="budget_extension",
                    action_description=gate_message,
                    action_payload={
                        "step": step.value,
                        "cost_usd": state.cost_usd,
                        "max_cost_usd": state.budget.max_cost_usd,
                        "budget_remaining": budget_remaining,
                    },
                )
                raise ApprovalGateError(approval.id, step.value, gate_message)

        try:
            if self.safety_service:
                await enforce_step_safety_gate(
                    safety_service=self.safety_service,
                    project_id=state.project_id,
                    run_id=self.run_id,
                    step=step.value,
                    current_cost_usd=state.cost_usd,
                    project_settings=self.project_safety_settings,
                )
        except ApprovalGateError:
            if self.run_service and self.run_id:
                try:
                    await self.run_service.update_run(
                        self.run_id,
                        ResearchRunUpdate(state="waiting_for_approval", current_phase=step.value),
                    )
                except Exception as update_error:
                    logger.warning("update_run_waiting_failed", error=str(update_error), exc_info=True)
            raise

        # Update current phase in DB
        if self.run_service and self.run_id:
            try:
                await self.run_service.update_run(
                    self.run_id,
                    ResearchRunUpdate(current_phase=step.value),
                )
            except Exception as e:
                logger.warning("update_run_phase_failed", error=str(e), exc_info=True)

        # Broadcast step progress
        await self._broadcast_event(
            "step_started",
            details={
                "step": step.value,
                "label": self._phase_label(step),
            },
        )

        try:
            # Execute handler
            state = await handler(state)

            # Strict Protocol Validation
            issues = state.validate_consistency()
            if issues:
                logger.warning("state_consistency_issues", step=step.value, issues=issues)
                for issue in issues:
                    state.warnings.append(f"Consistency: {issue}")

            # Record cost for gated steps (spend tracking)
            if self.safety_service and step.value in GATED_STEPS:
                step_cost = STEP_COST_ESTIMATES.get(step.value, 0.0)
                self.safety_service.record_cost(state.project_id, step_cost)
                state.cost_usd += step_cost

            # Record success
            duration = (datetime.now() - start_time).total_seconds()
            result = WorkflowStepResult(
                step=step,
                status="completed",
                duration_seconds=duration,
            )
            self.step_history.append(result)
            await self._persist_step_history()

            await self._broadcast_event(
                "step_completed",
                details={"step": step.value, "duration": round(duration, 2), "phase_label": self._phase_label(step)},
            )

            # Record tool call
            if self.run_service and self.run_id:
                try:
                    agent_role = self._step_to_agent(step)
                    await self.run_service.add_tool_call(
                        run_id=self.run_id,
                        tool_name=f"step_{step.value}",
                        agent_role=agent_role,
                        duration_ms=int(duration * 1000),
                        success=True,
                    )
                except Exception as e:
                    logger.debug("tool_call_record_failed", tool_name=f"step_{step.value}", error=str(e))

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            result = WorkflowStepResult(
                step=step,
                status="failed",
                duration_seconds=duration,
                error=str(e),
            )
            self.step_history.append(result)
            await self._persist_step_history()
            state.add_error(f"step_failed_{step.value}", str(e))
            logger.error("step_failed", step=step.value, error=str(e))

            if required:
                raise RuntimeError(f"Required workflow step '{step.value}' failed: {e!s}") from e

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
        if output.reasoning:
            await self._broadcast_thought(output.reasoning, actor=agent.name)
        state.current_phase = "intent_interpreted"
        return state

    async def _plan_search(self, state: ResearchState) -> ResearchState:
        """Plan literature search — expand keywords and broadcast them."""
        await self._broadcast_thought("Analyzing research idea to expand search space...")
        keywords = None
        if self.keyword_engine:
            try:
                kw_result = await self.keyword_engine.expand_keywords(state.current_idea)
                all_terms = []
                all_terms.extend(kw_result.core_concepts)
                all_terms.extend(kw_result.synonyms)
                all_terms.extend(kw_result.method_terms)
                if self._is_flexible_mode():
                    all_terms.extend(kw_result.adjacent_field_terms)
                    all_terms.extend(kw_result.application_terms)
                    all_terms.extend(kw_result.metric_terms)
                keywords = all_terms or None
            except Exception as e:
                logger.warning("keyword_expansion_failed", error=str(e), exc_info=True)

        # Store keywords in state for use by _retrieve_literature
        state.keywords = keywords or []

        await self._broadcast_thought(f"Identified {len(state.keywords)} conceptual vectors for exploration.")

        # Broadcast keywords event
        await self._broadcast_event(
            "keywords",
            details={
                "idea": state.current_idea,
                "keywords": state.keywords,
            },
        )

        state.current_phase = "search_planned"
        return state

    async def _retrieve_literature(self, state: ResearchState) -> ResearchState:
        """Retrieve literature by searching academic databases."""
        from app.schemas.research_state import PaperSummary

        await self._broadcast_thought("Initializing federated search across academic and web sources...")

        if not self.literature_engine:
            logger.warning("no_literature_engine")
            state.current_phase = "literature_retrieved"
            return state

        # Use keywords from state (expanded in _plan_search)
        keywords = state.keywords or None

        # Broadcast search start
        sources = list(self.connectors.connectors.keys()) if self.connectors else []
        await self._broadcast_event(
            "search_started",
            details={
                "sources": sources,
                "query": " ".join((keywords or [])[:5]),
                "max_results": self._literature_limit(state),
            },
        )

        # Search academic databases
        try:
            await self._broadcast_thought(f"Executing search queries across {len(sources)} connectors...")
            from datetime import datetime

            year_span = self._literature_year_span()
            result = await self.literature_engine.retrieve_literature(
                idea=state.current_idea,
                keywords=keywords,
                year_from=datetime.now().year - year_span,
                limit=self._literature_limit(state),
            )

            await self._broadcast_thought(f"Successfully harvested {len(result.papers)} nodes from the global corpus. Beginning relevance scoring.")

            # Broadcast results summary
            await self._broadcast_event(
                "search_results",
                details={
                    "total_found": result.total_found,
                    "papers_count": len(result.papers),
                    "search_queries": result.search_queries_used,
                },
            )

            # Convert found papers to PaperSummary and add to state
            for rp in result.papers:
                paper = rp.paper
                paper_id = paper.source_id or paper.doi or paper.title[:50]
                state.papers.append(
                    PaperSummary(
                        id=paper_id,
                        title=paper.title,
                        authors=paper.authors if isinstance(paper.authors, list) else [str(paper.authors)],
                        year=paper.year,
                        doi=paper.doi,
                        citation_count=paper.citation_count,
                        paper_type=paper.paper_type,
                        relevance_score=rp.overall_score,
                        references=paper.references or [],
                    ),
                )

                # Broadcast each paper found
                await self._broadcast_event(
                    "paper_found",
                    details={
                        "id": paper_id,
                        "title": paper.title,
                        "authors": paper.authors[:3] if isinstance(paper.authors, list) else [],
                        "year": paper.year,
                        "source": paper.source,
                        "doi": paper.doi,
                        "url": paper.url,
                    },
                )

            state.sources_searched += result.total_found
            logger.info(
                "literature_retrieved",
                papers_found=len(result.papers),
                total_sources=result.total_found,
            )

        except Exception as e:
            logger.error("literature_retrieval_failed", error=str(e), exc_info=True)
            state.add_error("literature_retrieval", str(e))

        # Broadcast completion
        await self._broadcast_event(
            "search_complete",
            details={
                "papers_count": len(state.papers),
            },
        )

        state.current_phase = "literature_retrieved"
        return state

    async def _analyze_papers(self, state: ResearchState) -> ResearchState:
        """Analyze papers using the analysis engine."""
        await self._broadcast_thought("Commencing deep semantic analysis of the discovered corpus...")
        if not self.analysis_engine or not state.papers:
            state.current_phase = "papers_analyzed"
            return state

        try:
            # Analyze up to 10 papers (in-memory analysis only)
            for paper_summary in state.papers[:10]:
                try:
                    analysis = await self.analysis_engine.analyze_paper(
                        paper_id=paper_summary.id,
                        title=paper_summary.title,
                        abstract="",  # Would need full paper data
                        idea_context=state.current_idea,
                    )
                    if analysis:
                        state.add_event("paper_analyzed", details={"paper": paper_summary.title[:80]})
                except Exception as e:
                    logger.warning("paper_analysis_failed", paper=paper_summary.title[:50], error=str(e), exc_info=True)

            state.add_event("papers_analyzed", details={"count": min(len(state.papers), 10)})
            await self._broadcast_thought(f"Analysis complete for {min(len(state.papers), 10)} primary nodes. Semantic weights calibrated.")
        except Exception as e:
            logger.error("analysis_failed", error=str(e), exc_info=True)

        state.current_phase = "papers_analyzed"
        return state

    async def _cluster_papers(self, state: ResearchState) -> ResearchState:
        """Cluster papers using the clustering engine."""
        from app.schemas.research_state import ClusterSummary

        await self._broadcast_thought("Mapping topological landscape and identifying thematic clusters...")
        if not self.clustering_engine or not state.papers:
            state.current_phase = "papers_clustered"
            return state

        try:
            paper_dicts = [
                {"title": p.title, "id": p.id, "authors": p.authors, "year": p.year}
                for p in state.papers
            ]
            result = await self.clustering_engine.cluster_papers(
                papers=paper_dicts,
            )
            if result and hasattr(result, "clusters"):
                # Update cognitive health metrics
                state.cognitive_entropy = getattr(result, "cognitive_entropy", 0.0)
                state.cognitive_mode = getattr(result, "cognitive_mode", "exploration")

                for c in result.clusters[:10]:
                    state.clusters.append(
                        ClusterSummary(
                            id=c.id,
                            name=c.name,
                            description=c.description,
                            paper_count=len(c.paper_ids),
                            paper_ids=c.paper_ids,
                        ),
                    )
            state.add_event(
                "papers_clustered",
                details={
                    "clusters": len(state.clusters),
                    "entropy": state.cognitive_entropy,
                    "mode": state.cognitive_mode,
                },
            )
            await self._broadcast_event(
                "papers_clustered",
                details={
                    "clusters": len(state.clusters),
                    "entropy": state.cognitive_entropy,
                    "mode": state.cognitive_mode,
                },
            )
            await self._broadcast_cognitive_update(state)
        except Exception as e:
            logger.error("clustering_failed", error=str(e), exc_info=True)

        state.current_phase = "papers_clustered"
        return state

    async def _detect_conflicts(self, state: ResearchState) -> ResearchState:
        """Detect conflicts using the conflict engine."""
        from app.schemas.research_state import ConflictSummary

        await self._broadcast_thought("Scanning for epistemic tensions and methodological contradictions...")
        if not self.conflict_engine or len(state.papers) < 2:
            state.current_phase = "conflicts_detected"
            return state

        try:
            paper_dicts = [
                {"title": p.title, "authors": p.authors, "year": p.year, "id": p.id}
                for p in state.papers[:15]
            ]
            result = await self.conflict_engine.detect_conflicts(papers=paper_dicts)
            if result and hasattr(result, "conflicts"):
                for c in result.conflicts[:10]:
                    state.conflicts.append(
                        ConflictSummary(
                            id=c.id,
                            conflict_type=c.conflict_type,
                            description=c.description,
                            severity=c.severity,
                        ),
                    )
        except Exception as e:
            logger.error("conflict_detection_failed", error=str(e), exc_info=True)

        state.current_phase = "conflicts_detected"
        return state

    async def _generate_questions(self, state: ResearchState) -> ResearchState:
        """Generate research questions using the question engine."""
        from app.engine.conflict_detection import Conflict
        from app.schemas.research_state import QuestionSummary

        await self._broadcast_thought("Synthesizing research questions to bridge identified knowledge gaps...")
        if not self.question_engine:
            state.current_phase = "questions_generated"
            return state

        try:
            # Convert state conflicts to engine Conflict objects
            conflict_objs = [
                Conflict(
                    id=c.id or f"conflict-{i}",
                    conflict_type=c.conflict_type,
                    description=c.description,
                    severity=c.severity or 0.5,
                )
                for i, c in enumerate(state.conflicts)
            ]
            gap_objs = []  # No gaps from our pipeline yet

            result = await self.question_engine.generate_questions(
                conflicts=conflict_objs,
                gaps=gap_objs,
                idea_context=state.current_idea,
            )
            if result and hasattr(result, "questions"):
                for q in result.questions[:10]:
                    state.questions.append(
                        QuestionSummary(
                            id=q.id,
                            question=q.question,
                            rank=q.overall_score,
                            status="active",
                        ),
                    )
        except Exception as e:
            logger.error("question_generation_failed", error=str(e), exc_info=True)

        state.current_phase = "questions_generated"
        return state

    async def _form_hypotheses(self, state: ResearchState) -> ResearchState:
        """Form hypotheses using the hypothesis engine."""
        from app.schemas.research_state import HypothesisSummary

        await self._broadcast_thought("Forging testable hypotheses from prioritized inquiries...")
        if not self.hypothesis_engine:
            state.current_phase = "hypotheses_formed"
            return state

        try:
            question_dicts = [
                {"id": q.id, "question": q.question, "rank": q.rank}
                for q in state.questions
            ]
            result = await self.hypothesis_engine.generate_hypotheses(
                questions=question_dicts,
                idea_context=state.current_idea,
            )
            if result and hasattr(result, "hypotheses"):
                for h in result.hypotheses:
                    state.hypotheses.append(
                        HypothesisSummary(
                            id=h.id if hasattr(h, "id") else "",
                            statement=h.statement if hasattr(h, "statement") else str(h),
                            confidence=h.confidence if hasattr(h, "confidence") else 0.5,
                            status="draft",
                        ),
                    )
        except Exception as e:
            logger.error("hypothesis_generation_failed", error=str(e), exc_info=True)

        state.current_phase = "hypotheses_formed"

        # Capture sub-ideas from promising hypotheses
        await self._capture_sub_ideas(state)

        return state

    async def _capture_sub_ideas(self, state: ResearchState):
        """Capture sub-ideas from hypotheses and questions that suggest new directions."""
        if not state.hypotheses or not state.idea_id:
            return

        try:
            from sqlalchemy import select

            from app.models.idea import Idea as IdeaModel
            from app.services.idea_ledger_service import IdeaLedgerService

            idea_ledger = IdeaLedgerService(self.db)

            # Find high-confidence hypotheses that suggest new research directions
            for hyp in state.hypotheses:
                if hyp.confidence and hyp.confidence >= 0.6:
                    # Check if this hypothesis already generated a sub-idea
                    existing = await self.db.execute(
                        select(IdeaModel).where(
                            IdeaModel.parent_idea_id == state.idea_id,
                            IdeaModel.current_text.like(f"%{hyp.statement[:50]}%"),
                        ).limit(1),
                    )
                    if existing.scalar_one_or_none():
                        continue

                    # Create sub-idea
                    sub_text = f"Investigate: {hyp.statement}\n\nThis emerged as a promising hypothesis (confidence: {hyp.confidence:.2f}) during research on: {state.current_idea[:200]}"
                    sub_idea = await idea_ledger.create_idea(
                        project_id=state.project_id,
                        text=sub_text,
                        origin="skill_generated",
                        flexibility=0.7,
                    )
                    # Link to parent
                    await self.db.execute(
                        __import__("sqlalchemy").update(IdeaModel)
                        .where(IdeaModel.id == sub_idea.id)
                        .values(parent_idea_id=state.idea_id),
                    )
                    state.add_event("sub_idea_captured", details={
                        "sub_idea_id": sub_idea.id,
                        "parent_idea_id": state.idea_id,
                        "hypothesis": hyp.statement[:100],
                    })
                    logger.info("sub_idea_captured", sub_idea_id=sub_idea.id, hypothesis=hyp.statement[:80])
        except Exception as e:
            logger.warning("sub_idea_capture_failed", error=str(e), exc_info=True)

    async def _plan_validation(self, state: ResearchState) -> ResearchState:
        """Plan validation using the validation engine.

        Captures feasibility scores into state.validation_plans so the scoring
        engine can incorporate them when evaluating idea quality.
        """
        if not self.validation_engine or not state.hypotheses:
            state.current_phase = "validation_planned"
            return state

        try:
            for h in state.hypotheses[:5]:
                try:
                    plan = await self.validation_engine.create_validation_plan(
                        hypothesis={"id": h.id, "statement": h.statement, "confidence": h.confidence},
                        idea_context=state.current_idea,
                    )
                    # Capture plan for scoring engine AND experiment code generator
                    state.validation_plans.append({
                        "id": plan.id,
                        "hypothesis_id": plan.hypothesis_id or h.id,
                        "hypothesis_statement": h.statement,
                        "feasibility_score": plan.feasibility_score,
                        "difficulty_estimate": plan.difficulty_estimate,
                        "cost_estimate": plan.cost_estimate,
                        "dataset_candidates": [
                            {
                                "name": d.name,
                                "source": d.source,
                                "url": d.url,
                                "description": d.description,
                                "size": d.size,
                                "format": d.format,
                            }
                            for d in plan.dataset_candidates
                        ],
                        "benchmark_candidates": plan.benchmark_candidates,
                        "baselines": plan.baselines,
                        "metrics": plan.metrics,
                        "statistical_tests": plan.statistical_tests,
                        "experimental_design": plan.experimental_design,
                        "simulation_option": plan.simulation_option,
                        "expected_artifacts": plan.expected_artifacts,
                        "time_estimate": plan.time_estimate,
                        "requirements": plan.requirements,
                        "risks": plan.risks,
                        "notes": plan.notes,
                    })
                    # Mark hypothesis as having a validation plan
                    h.has_validation_plan = True
                    state.add_event("validation_planned", details={
                        "hypothesis": h.statement[:80],
                        "feasibility": plan.feasibility_score,
                    })
                except Exception as e:
                    logger.warning("validation_plan_failed", error=str(e), exc_info=True)
                    state.validation_plans.append({
                        "hypothesis_id": h.id,
                        "hypothesis_statement": h.statement,
                        "feasibility_score": None,
                        "error": str(e),
                    })
        except Exception as e:
            logger.error("validation_planning_failed", error=str(e), exc_info=True)

        state.current_phase = "validation_planned"
        return state

    async def _score_idea(self, state: ResearchState) -> ResearchState:
        """Score the idea quality using the scoring engine.

        Incorporates validation plan feasibility scores when available.
        """
        from app.schemas.research_state import ScoreSummary

        await self._broadcast_thought("Quantifying research value and epistemic potential...")
        if not self.scoring_engine:
            state.current_phase = "idea_scored"
            return state

        try:
            # Build paper and conflict dicts for scoring
            paper_dicts = [{"title": p.title, "year": p.year} for p in state.papers]
            conflict_dicts = [{"type": c.conflict_type, "description": c.description} for c in state.conflicts]

            # Build validation_plan dict from captured plans (if any)
            validation_plan_dict = None
            if state.validation_plans:
                best_plan = max(
                    state.validation_plans,
                    key=lambda p: p.get("feasibility_score") or 0,
                )
                validation_plan_dict = {
                    "feasibility_score": best_plan.get("feasibility_score"),
                    "difficulty_estimate": best_plan.get("difficulty_estimate"),
                    "cost_estimate": best_plan.get("cost_estimate"),
                    "plan_count": len(state.validation_plans),
                }

            score_result = await self.scoring_engine.score_idea(
                idea={"id": state.idea_id or "", "current_text": state.current_idea},
                papers=paper_dicts or None,
                conflicts=conflict_dicts or None,
                validation_plan=validation_plan_dict,
            )
            if score_result:
                state.scores.append(
                    ScoreSummary(
                        id=getattr(score_result, "idea_id", "") or getattr(score_result, "id", ""),
                        novelty=getattr(score_result, "novelty", None),
                        feasibility=getattr(score_result, "feasibility", None),
                        importance=getattr(score_result, "importance", None),
                        evidence_support=getattr(score_result, "evidence_support", None),
                        validation_clarity=getattr(score_result, "validation_clarity", None),
                        differentiation=getattr(score_result, "differentiation", None),
                        data_availability=getattr(score_result, "data_availability", None),
                        skill_leverage=getattr(score_result, "skill_leverage", None),
                        user_alignment=getattr(score_result, "user_alignment", None),
                        prior_art_risk=getattr(score_result, "prior_art_risk", None),
                        safety_risk=getattr(score_result, "safety_risk", None),
                        cost_risk=getattr(score_result, "cost_risk", None),
                        overall_value=getattr(score_result, "overall_value", None),
                        classification=getattr(score_result, "classification", None),
                        rationale=getattr(score_result, "rationale", None),
                    ),
                )
                state.current_classification = getattr(score_result, "classification", None)
        except Exception as e:
            logger.error("scoring_failed", error=str(e), exc_info=True)

        state.current_phase = "idea_scored"
        return state

    async def _make_decision(self, state: ResearchState) -> ResearchState:
        """Make decision on next action and store it."""
        await self._broadcast_thought("Finalizing cognitive consensus and research direction...")
        try:
            classification = state.current_classification or "pending"
            # Map classification to valid decision type
            decision_map = {
                "strong": "promote", "promising": "continue", "moderate": "continue",
                "weak": "revise", "poor": "archive", "pending": "continue",
            }
            decision_type = decision_map.get(classification, "continue")
            if self.idea_ledger:
                await self.idea_ledger.add_decision(
                    idea_id=state.idea_id,
                    decision=decision_type,
                    reason=f"{len(state.papers)} papers, {len(state.questions)} questions, {len(state.hypotheses)} hypotheses. Classification: {classification}",
                    run_id=state.run_id,
                )
            state.add_event("decision_recorded", details={"classification": classification, "decision": decision_type})
        except Exception as e:
            logger.warning("decision_recording_failed", error=str(e), exc_info=True)

        state.current_phase = "decision_made"
        return state

    async def _create_skills(self, state: ResearchState) -> ResearchState:
        """Create skills from successful patterns."""
        await self._broadcast_thought("Abstracting successful research patterns into reusable skill units...")
        try:
            from uuid import uuid4

            from app.models.skill import Skill as SkillModel

            # Create a skill based on the research context
            steps_completed = [s.step.value for s in self.step_history if s.status == "completed"]
            if steps_completed:
                skill = SkillModel(
                    id=str(uuid4()),
                    project_id=state.project_id,
                    name=f"Research: {state.current_idea[:60]}",
                    skill_type="functional",
                    purpose=f"Completed research workflow with {len(state.papers)} papers analyzed across {len(steps_completed)} steps",
                    procedure=steps_completed[:10],
                    inputs=[state.current_idea],
                    outputs=[f"{len(state.papers)} papers", f"{len(state.clusters)} clusters", f"{len(state.hypotheses)} hypotheses"],
                    trigger_conditions=["user_directed"],
                    status="candidate",
                )
                self.db.add(skill)
                state.add_event("skill_created", details={"skill_name": skill.name})
        except Exception as e:
            logger.warning("skill_creation_failed", error=str(e), exc_info=True)

        state.current_phase = "skills_created"
        return state

    async def _generate_report(self, state: ResearchState) -> ResearchState:
        """Generate research report."""
        await self._broadcast_thought("Archiving research cycle and generating comprehensive report...")
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
        if output.reasoning:
            await self._broadcast_thought(output.reasoning, actor=agent.name)
        state.current_phase = "report_generated"
        return state

    async def _generate_experiment(self, state: ResearchState) -> ResearchState:
        """Generate executable experiment code based on validation plans.

        Uses a three-tier strategy:
        1. Sandbox script generator (template-driven, deterministic) — preferred
           when a validation plan exists with datasets, metrics, and tests.
        2. LLM agent (flexible, exploratory) — fallback when no validation plan
           is available or when creative code generation is needed.
        3. ``_fallback_experiment_code`` — last resort minimal scaffold.
        """
        await self._broadcast_thought("Translating validation protocols into executable experiment logic...")

        primary_hypothesis = state.hypotheses[0].statement if state.hypotheses else state.current_idea
        generated_code: str | None = None
        requirements: list[str] = []

        # ── Tier 1: Sandbox script generator (template-driven) ──────────
        if state.validation_plans:
            primary_plan = state.validation_plans[0]
            try:
                from app.engine.sandbox_generator import get_sandbox_generator

                gen = get_sandbox_generator()
                # Use the first hypothesis ID, or a placeholder when unavailable
                hyp_id = state.hypotheses[0].id if state.hypotheses else "unknown"

                result = await gen.generate_script(
                    hypothesis_id=hyp_id,
                    hypothesis_statement=primary_hypothesis,
                    validation_plan=primary_plan,
                )
                generated_code = result["script_content"]

                # The generated template uses numpy + pandas unconditionally;
                # scipy is needed when statistical tests are specified.
                requirements = ["numpy", "pandas"]
                if primary_plan.get("statistical_tests"):
                    requirements.append("scipy")

                # Merge any additional requirements from the validation plan
                plan_reqs = primary_plan.get("requirements", [])
                if plan_reqs:
                    requirements = list(set(requirements) | set(plan_reqs))

                logger.info(
                    "experiment_using_template",
                    hypothesis=primary_hypothesis[:80],
                    template_length=len(generated_code),
                )
            except Exception as exc:
                logger.warning(
                    "sandbox_generator_failed",
                    error=str(exc),
                    exc_info=True,
                    msg="Falling back to LLM code generation",
                )
                generated_code = None

        # ── Tier 2: LLM agent (exploratory / creative code) ─────────────
        if not generated_code:
            # Build validation plan context for LLM (may be empty)
            validation_plan_context: dict[str, Any] = {}
            if state.validation_plans:
                primary_plan = state.validation_plans[0]
                validation_plan_context = {
                    "datasets": primary_plan.get("dataset_candidates", []),
                    "baselines": primary_plan.get("baselines", []),
                    "metrics": primary_plan.get("metrics", []),
                    "statistical_tests": primary_plan.get("statistical_tests", []),
                    "experimental_design": primary_plan.get("experimental_design", ""),
                }
                plan_reqs = primary_plan.get("requirements", [])
                if plan_reqs:
                    requirements = list(set(requirements) | set(plan_reqs))

            agent = self.agents.get(AgentRole.DEVELOPER)
            if agent:
                input = AgentInput(
                    task=(
                        "Generate a self-contained Python script to validate the primary hypothesis. "
                        "At the end, print ##HYPOTHESIS_RESULTS## followed by a JSON block "
                        'with key "hypothesis_results" — a list of per-hypothesis objects '
                        "with fields: hypothesis_id, statement, status (validated/rejected/inconclusive), "
                        "confidence (0-1), evidence (dict), p_value, significant_05. "
                        "Return only the script inside a ```python fenced block."
                    ),
                    context={
                        "hypotheses": [h.model_dump() for h in state.hypotheses],
                        "idea": state.current_idea,
                        "validation_plan": validation_plan_context,
                    },
                )
                output = await agent.run(input)
                if output.reasoning:
                    await self._broadcast_thought(output.reasoning, actor=agent.name)
                generated_code = _extract_python_code(output.content)

        # ── Tier 3: Deterministic synthetic scaffold ────────────────────
        if not generated_code:
            generated_code = _fallback_experiment_code(primary_hypothesis)
            logger.info("experiment_using_fallback", hypothesis=primary_hypothesis[:80])

        state.experiment_code = generated_code
        state.experiment_requirements = requirements
        state.add_event(
            "experiment_generated",
            details={"code_length": len(generated_code), "has_requirements": bool(requirements)},
        )
        await self._broadcast_event(
            "experiment_generated",
            details={"code_length": len(generated_code)},
        )
        return state

    async def _run_experiment(self, state: ResearchState) -> ResearchState:
        """Execute generated code in the isolated sandbox.

        Uses Docker for isolation with a local subprocess fallback when Docker
        is not available (development mode only). In production, Docker is required.
        """
        from app.config import get_settings
        from app.sandbox.executor import SandboxExecutor, SandboxResult

        settings = get_settings()
        executor = SandboxExecutor(
            docker_image=settings.sandbox_docker_image,
            timeout_seconds=settings.sandbox_timeout_seconds,
            memory_limit=settings.sandbox_memory_limit,
            cpu_limit=settings.sandbox_cpu_limit,
        )

        code = state.experiment_code or _fallback_experiment_code(
            state.hypotheses[0].statement if state.hypotheses else state.current_idea,
        )

        # Inject validation plan + hypothesis context into the sandbox code
        import json as _json

        # Hypothesis context: all hypothesis IDs and statements
        hyp_context = [
            {"id": h.id, "statement": h.statement, "confidence": h.confidence}
            for h in state.hypotheses
        ]
        hyp_context_json = _json.dumps(hyp_context, indent=2)

        # Validation plan context (primary plan, may be empty)
        plan_json = _json.dumps({})
        if state.validation_plans:
            primary = state.validation_plans[0]
            plan_json = _json.dumps(
                {
                    "hypothesis_statement": primary.get("hypothesis_statement", ""),
                    "dataset_candidates": primary.get("dataset_candidates", []),
                    "baselines": primary.get("baselines", []),
                    "metrics": primary.get("metrics", []),
                    "statistical_tests": primary.get("statistical_tests", []),
                    "experimental_design": primary.get("experimental_design", ""),
                    "requirements": primary.get("requirements", []),
                },
                indent=2,
            )

        code = f"""# --- Workflow context (injected by workflow) ---
import json as _vp_json
VALIDATION_PLAN = _vp_json.loads(_vp_json.dumps({plan_json}))
HYPOTHESES = _vp_json.loads(_vp_json.dumps({hyp_context_json}))
_VP_DATASETS = VALIDATION_PLAN.get("dataset_candidates", [])
_VP_BASELINES = VALIDATION_PLAN.get("baselines", [])
_VP_METRICS = VALIDATION_PLAN.get("metrics", [])
_VP_TESTS = VALIDATION_PLAN.get("statistical_tests", [])
_VP_DESIGN = VALIDATION_PLAN.get("experimental_design", "")
# --- end workflow context ---

{code}
"""

        # Attempt sandbox execution with fallback for dev mode
        try:
            result = await executor.run_python(
                code,
                requirements=state.experiment_requirements or None,
            )
        except FileNotFoundError:
            # Docker is required for isolated sandbox execution. Never fall back
            # to running experiment code on the host (would be a remote-code
            # execution risk). Fail the experiment instead.
            logger.error("sandbox_docker_unavailable", env=settings.app_env)
            result = SandboxResult(
                success=False,
                stdout="",
                stderr="Docker is required to execute experiments in an isolated sandbox.",
                exit_code=-1,
                duration_ms=0,
                error_message="Docker unavailable",
            )

        state.experiment_result = {
            "success": result.success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
            "duration_ms": result.duration_ms,
            "error_message": result.error_message,
        }

        if self.db and state.run_id:
            try:
                from app.models.report import AnalysisArtifact, AnalysisRun

                analysis_run = AnalysisRun(
                    id=str(uuid4()),
                    run_id=state.run_id,
                    hypothesis_id=state.hypotheses[0].id if state.hypotheses else None,
                    script=code,
                    status="completed" if result.success else "failed",
                    error_message=result.error_message,
                )
                self.db.add(analysis_run)
                await self.db.flush()

                self.db.add(
                    AnalysisArtifact(
                        id=str(uuid4()),
                        analysis_run_id=analysis_run.id,
                        artifact_type="stdout",
                        description=result.stdout[:4000] if result.stdout else None,
                    ),
                )
                await self.db.flush()
            except Exception as e:
                logger.warning("persist_analysis_run_failed", error=str(e), exc_info=True)

        state.add_event(
            "experiment_completed",
            details={
                "success": result.success,
                "stdout": result.stdout[:500],
                "duration": result.duration_ms,
            },
        )
        await self._broadcast_event(
            "experiment_completed",
            details={
                "success": result.success,
                "stdout_preview": result.stdout[:200],
            },
        )
        return state


    async def _validate_hypotheses(self, state: ResearchState) -> ResearchState:
        """Validate hypotheses against experiment results.

        First attempts to parse structured per-hypothesis results from
        experiment stdout (##HYPOTHESIS_RESULTS## marker). Falls back to
        a single boolean applied to all hypotheses when no structured
        data is found.
        """
        import json as _json

        await self._broadcast_thought("Reconciling experimental evidence with stated hypotheses...")

        if not state.experiment_result or not state.hypotheses:
            state.current_phase = "hypotheses_validated"
            return state

        experiment_success = state.experiment_result.get("success", False)
        stdout = state.experiment_result.get("stdout", "")
        stderr = state.experiment_result.get("stderr", "")
        error_message = state.experiment_result.get("error_message")

        # ── Stage 1: Parse structured per-hypothesis results ──────────────
        # Expected stdout format:
        #   ##HYPOTHESIS_RESULTS##
        #   {"hypothesis_results": [{"hypothesis_id": "...", "status": "...", ...}]}
        per_hyp_results: list[dict[str, Any]] = []
        if stdout:
            hyp_results_match = re.search(
                r"##HYPOTHESIS_RESULTS##\s*\n(.+?)(?:\n>>>|\n##|\Z)",
                stdout,
                re.DOTALL,
            )
            if hyp_results_match:
                try:
                    parsed = _json.loads(hyp_results_match.group(1))
                    per_hyp_results = parsed.get("hypothesis_results", [])
                except (_json.JSONDecodeError, TypeError, KeyError) as exc:
                    logger.warning("hypothesis_results_parse_failed", error=str(exc))

        # Build lookup from hypothesis ID -> structured result
        hyp_result_map: dict[str, dict[str, Any]] = {}
        for r in per_hyp_results:
            rid = r.get("hypothesis_id") or ""
            if rid:
                hyp_result_map[rid] = r

        # ── Stage 2: Update each hypothesis ───────────────────────────────
        for hyp in state.hypotheses:
            # Prefer per-hypothesis result above single-boolean heuristic
            result = hyp_result_map.get(hyp.id)

            if result:
                # Structured per-hypothesis result
                new_status = result.get("status", "inconclusive")
                if new_status not in ("validated", "rejected", "inconclusive"):
                    new_status = "inconclusive"

                parsed_confidence = result.get("confidence")
                if parsed_confidence is not None:
                    confidence_delta = parsed_confidence - (hyp.confidence or 0.5)
                else:
                    confidence_delta = 0.0

                # Build reasoning from structured evidence
                result.get("evidence", {})
                p_val = result.get("p_value")
                sig = result.get("significant_05")
                parts = [f"Per-hypothesis result: {new_status}"]
                if p_val is not None:
                    parts.append(f"p={p_val:.4f}")
                if sig is not None:
                    parts.append(f"significant_05={sig}")
                reasoning = "; ".join(parts)
            # Fallback: single boolean applied uniformly
            elif experiment_success:
                new_status = "validated"
                confidence_delta = 0.15
                reasoning = (
                    f"Experiment completed successfully (single-boolean fallback). "
                    f"Output preview: {stdout[:300]}"
                )
            else:
                new_status = "rejected"
                confidence_delta = -0.20
                reasoning = (
                    f"Experiment failed (single-boolean fallback). "
                    f"Error: {error_message or stderr[:300]}"
                )

            # Update status in the in-memory state
            hyp.status = new_status
            if hyp.confidence is not None:
                hyp.confidence = max(0.0, min(1.0, hyp.confidence + confidence_delta))

            # Persist update to DB
            if self.run_service and self.run_id:
                try:
                    from sqlalchemy import update

                    from app.models.research_question import Hypothesis as HypothesisModel

                    stmt = (
                        update(HypothesisModel)
                        .where(HypothesisModel.id == hyp.id)
                        .values(status=new_status, confidence=hyp.confidence)
                    )
                    await self.db.execute(stmt)
                except Exception as e:
                    logger.warning("hypothesis_update_failed", hypothesis_id=hyp.id, error=str(e), exc_info=True)

            state.hypothesis_validation_results.append({
                "hypothesis_id": hyp.id,
                "statement": hyp.statement[:200],
                "new_status": new_status,
                "reasoning": reasoning,
                "used_per_hypothesis_result": result is not None,
            })

            state.add_event("hypothesis_validated", details={
                "hypothesis": hyp.statement[:80],
                "status": new_status,
                "reasoning": reasoning[:120],
            })

        await self._broadcast_event(
            "hypotheses_validated",
            details={
                "total": len(state.hypotheses),
                "validated": sum(1 for r in state.hypothesis_validation_results if r.get("new_status") == "validated"),
                "rejected": sum(1 for r in state.hypothesis_validation_results if r.get("new_status") == "rejected"),
                "structured_results_parsed": bool(per_hyp_results),
            },
        )

        logger.info(
            "hypotheses_validated",
            count=len(state.hypothesis_validation_results),
            structured_parsed=bool(per_hyp_results),
            structured_count=len(per_hyp_results),
        )

        # ── Stage 3: Propagate experiment feedback back into scores ──────
        # Update state.scores[0] with experiment-derived metrics so the
        # persistence layer writes them into the IdeaScore record.
        from app.schemas.research_state import ScoreSummary

        if state.scores:
            validated_count = sum(
                1 for r in state.hypothesis_validation_results
                if r.get("new_status") == "validated"
            )
            rejected_count = sum(
                1 for r in state.hypothesis_validation_results
                if r.get("new_status") == "rejected"
            )
            total = len(state.hypothesis_validation_results)
            success_rate = validated_count / max(total, 1)

            # Compute average confidence from updated hypotheses
            hyp_confidences = [h.confidence for h in state.hypotheses if h.confidence is not None]
            avg_confidence = sum(hyp_confidences) / max(len(hyp_confidences), 1) if hyp_confidences else 0.5

            # evidence_support: blend of validation success rate + hypothesis confidence
            new_evidence_support = 0.3 * success_rate + 0.7 * avg_confidence

            # validation_clarity: 1.0 if structured results, 0.3 if fallback, 0.0 if no experiment
            has_structured = bool(per_hyp_results)
            has_experiment = state.experiment_result is not None
            if has_structured:
                new_validation_clarity = 1.0
            elif has_experiment:
                new_validation_clarity = 0.3
            else:
                new_validation_clarity = 0.0

            # overall_value: blend of existing value with experimental evidence
            existing_value = state.scores[0].overall_value or 0.5
            new_overall_value = 0.6 * existing_value + 0.4 * new_evidence_support

            # Build experiment feedback dict for the score record
            experiment_feedback = {
                "hypotheses_validated": validated_count,
                "hypotheses_rejected": rejected_count,
                "hypotheses_total": total,
                "success_rate": round(success_rate, 4),
                "avg_confidence": round(avg_confidence, 4),
                "structured_results_parsed": has_structured,
                "experiment_success": state.experiment_result.get("success", False) if state.experiment_result else None,
                "hypothesis_results": [
                    {
                        "hypothesis_id": r.get("hypothesis_id"),
                        "status": r.get("new_status"),
                        "used_structured": r.get("used_per_hypothesis_result", False),
                    }
                    for r in state.hypothesis_validation_results
                ],
            }

            # Update the in-memory score — this gets persisted by _persist_scores
            existing = state.scores[0]
            new_rationale = (
                f"{existing.rationale or 'Pre-experiment score'}. "
                f"Experiment: {validated_count}/{total} hypotheses validated, "
                f"avg confidence {avg_confidence:.2f}"
            )
            state.scores[0] = ScoreSummary(
                id=existing.id,
                novelty=existing.novelty,
                feasibility=existing.feasibility,
                importance=existing.importance,
                evidence_support=round(new_evidence_support, 4),
                validation_clarity=new_validation_clarity,
                differentiation=existing.differentiation,
                data_availability=existing.data_availability,
                skill_leverage=existing.skill_leverage,
                user_alignment=existing.user_alignment,
                prior_art_risk=existing.prior_art_risk,
                safety_risk=existing.safety_risk,
                cost_risk=existing.cost_risk,
                overall_value=round(new_overall_value, 4),
                classification=existing.classification,
                rationale=new_rationale[:500],
                scored_at=existing.scored_at,
                cost_usd=existing.cost_usd,
                experiment_feedback=experiment_feedback,
            )
            logger.info(
                "experiment_feedback_applied_to_score",
                evidence_support=round(new_evidence_support, 4),
                validation_clarity=new_validation_clarity,
                overall_value=round(new_overall_value, 4),
                validated=validated_count,
                total=total,
            )

        # ── Stage 4: Extract structured claims from experiment output ────
        try:
            from app.api.research import get_llm_router
            hypothesis_dicts = [
                {"id": h.id, "statement": h.statement, "confidence": h.confidence}
                for h in state.hypotheses
            ]
            claims_result = await extract_claims(
                experiment_result=state.experiment_result,
                hypotheses=hypothesis_dicts,
                llm_router=get_llm_router(),
            )
            # Store claims in state as serializable dicts
            state.claims = [
                {
                    "statement": c.statement,
                    "claim_type": c.claim_type,
                    "confidence": c.confidence,
                    "evidence": c.evidence,
                    "metric": c.metric,
                    "value": c.value,
                    "source_hypothesis_id": c.source_hypothesis_id,
                    "source_hypothesis_statement": c.source_hypothesis_statement,
                }
                for c in claims_result.claims
            ]
            if claims_result.claims:
                logger.info(
                    "claims_extracted",
                    count=len(claims_result.claims),
                    llm_used=claims_result.llm_used,
                )
                await self._broadcast_event(
                    "claims_extracted",
                    details={
                        "count": len(claims_result.claims),
                        "llm_used": claims_result.llm_used,
                        "notes": claims_result.extraction_notes,
                    },
                )
        except Exception as e:
            logger.warning("claim_extraction_failed", error=str(e), exc_info=True)
            state.add_error("claim_extraction", str(e))

        state.current_phase = "hypotheses_validated"
        return state

    async def _generate_manuscript(self, state: ResearchState) -> ResearchState:
        """Generate a scientific LaTeX manuscript with real experiment and citation data."""
        await self._broadcast_thought("Synthesizing research findings into formal LaTeX manuscript structure...")

        if not self.db or not state.run_id:
            logger.warning("manuscript_generation_skipped", reason="missing_db_or_run_id")
            return state

        try:
            from app.api.research import get_llm_router
            from app.services.manuscript_service import ManuscriptService

            service = ManuscriptService(self.db, get_llm_router())
            manuscript = await service.generate_for_run(
                state.run_id,
                experiment_result=state.experiment_result,
            )
            await self._broadcast_event(
                "manuscript_generated",
                details={
                    "manuscript_id": manuscript.id,
                    "title": manuscript.title,
                    "has_references": bool(manuscript.bibtex),
                },
            )
            state.add_event(
                "manuscript_drafted",
                details={"manuscript_id": manuscript.id, "title": manuscript.title},
            )
        except Exception as e:
            logger.warning("manuscript_generation_failed", error=str(e), exc_info=True)
            state.add_error("manuscript_generation_failed", str(e))

        return state

    def pause(self, state: ResearchState | None = None) -> ResearchState | None:
        """Pause the workflow and propagate to the run state if provided."""
        self.status = WorkflowStatus.PAUSED
        if state is not None:
            state.state = RunState.PAUSED
            state.add_event("run_paused")
        return state

    def resume(self, state: ResearchState | None = None) -> ResearchState | None:
        """Resume the workflow and propagate to the run state if provided."""
        self.status = WorkflowStatus.RUNNING
        if state is not None:
            state.state = RunState.RUNNING
            state.add_event("run_resumed")
        return state

    def cancel(self, state: ResearchState | None = None) -> ResearchState | None:
        """Cancel the workflow and propagate to the run state if provided."""
        self.status = WorkflowStatus.CANCELLED
        if state is not None:
            state.state = RunState.CANCELLED
            state.add_event("run_cancelled")
        return state

    def get_step_history(self) -> list[WorkflowStepResult]:
        """Get the step history."""
        return self.step_history

    def get_total_duration(self) -> float:
        """Get total workflow duration."""
        return sum(s.duration_seconds for s in self.step_history)

    async def _broadcast_event(self, event_type: str, details: dict[str, Any] | None = None, actor: str = "system") -> None:
        """Persist event to DB and broadcast to live stream."""
        event_id = None

        # 1. Persist to DB
        if self.run_service and self.run_id:
            try:
                db_event = await self.run_service.add_run_event(
                    run_id=self.run_id,
                    event_type=event_type,
                    actor=actor,
                    details=details,
                )
                event_id = db_event.id
            except Exception as e:
                logger.warning("persist_event_failed", error=str(e), exc_info=True)

        # 2. Broadcast to live feed
        if self.event_broadcaster and self.run_id:
            try:
                await self.event_broadcaster.publish(
                    run_id=self.run_id,
                    event_type=event_type,
                    data=details,
                    event_id=event_id,
                )
            except Exception as e:
                logger.warning("broadcast_event_failed", error=str(e), exc_info=True)

    async def _broadcast_thought(self, thought: str, actor: str | None = None) -> None:
        """Broadcast an internal thinking event."""
        await self._broadcast_event(
            "thinking",
            details={"thought": thought},
            actor=actor or "system",
        )

    async def _persist_step_history(self) -> None:
        """Write workflow step history to the research run record."""
        if not self.run_service or not self.run_id:
            return
        try:
            await self.run_service.update_step_history(
                self.run_id,
                serialize_step_history(self.step_history),
            )
        except Exception as e:
            logger.warning("persist_step_history_failed", error=str(e), exc_info=True)

    async def _broadcast_cognitive_update(self, state: ResearchState) -> None:
        """Broadcast and persist live cognitive metrics."""
        if state.cognitive_entropy is None and state.cognitive_mode is None:
            return

        await self._broadcast_event(
            "cognitive_update",
            details={
                "entropy": state.cognitive_entropy,
                "mode": state.cognitive_mode,
            },
        )

        if self.run_service and self.run_id:
            try:
                await self.run_service.update_cognitive_metrics(
                    self.run_id,
                    cognitive_entropy=state.cognitive_entropy,
                    cognitive_mode=state.cognitive_mode,
                )
            except Exception as e:
                logger.warning("persist_cognitive_metrics_failed", error=str(e), exc_info=True)

    def _phase_label(self, step: WorkflowStep) -> str:
        """Human-readable phase label."""
        labels = {
            WorkflowStep.INTERPRET_INTENT: "Interpreting research intent",
            WorkflowStep.PLAN_SEARCH: "Planning literature search",
            WorkflowStep.RETRIEVE_LITERATURE: "Searching academic databases",
            WorkflowStep.ANALYZE_PAPERS: "Analyzing papers",
            WorkflowStep.CLUSTER_PAPERS: "Clustering papers by theme",
            WorkflowStep.DETECT_CONFLICTS: "Detecting conflicts in literature",
            WorkflowStep.GENERATE_QUESTIONS: "Generating research questions",
            WorkflowStep.FORM_HYPOTHESES: "Forming testable hypotheses",
            WorkflowStep.PLAN_VALIDATION: "Planning validation approach",
            WorkflowStep.SCORE_IDEA: "Scoring idea quality",
            WorkflowStep.MAKE_DECISION: "Making research decisions",
            WorkflowStep.GENERATE_EXPERIMENT: "Generating experiment code",
            WorkflowStep.RUN_EXPERIMENT: "Running sandboxed experiment",
            WorkflowStep.VALIDATE_HYPOTHESES: "Validating hypotheses against experiment results",
            WorkflowStep.CREATE_SKILLS: "Creating reusable research skills",
            WorkflowStep.GENERATE_MANUSCRIPT: "Generating LaTeX manuscript",
            WorkflowStep.GENERATE_REPORT: "Generating research report",
        }
        return labels.get(step, step.value)

    def _step_to_agent(self, step: WorkflowStep) -> str:
        """Map workflow step to agent role name."""
        mapping = {
            WorkflowStep.INTERPRET_INTENT: "user_intent",
            WorkflowStep.PLAN_SEARCH: "literature",
            WorkflowStep.RETRIEVE_LITERATURE: "literature",
            WorkflowStep.ANALYZE_PAPERS: "paper_analyst",
            WorkflowStep.CLUSTER_PAPERS: "cluster",
            WorkflowStep.DETECT_CONFLICTS: "conflict",
            WorkflowStep.GENERATE_QUESTIONS: "research_question",
            WorkflowStep.FORM_HYPOTHESES: "hypothesis",
            WorkflowStep.PLAN_VALIDATION: "validation_planner",
            WorkflowStep.SCORE_IDEA: "scoring",
            WorkflowStep.MAKE_DECISION: "decision",
            WorkflowStep.GENERATE_EXPERIMENT: "developer",
            WorkflowStep.RUN_EXPERIMENT: "data_analyst",
            WorkflowStep.VALIDATE_HYPOTHESES: "decision",
            WorkflowStep.CREATE_SKILLS: "skill_curator",
            WorkflowStep.GENERATE_MANUSCRIPT: "archivist",
            WorkflowStep.GENERATE_REPORT: "archivist",
        }
        return mapping.get(step, "workflow")
