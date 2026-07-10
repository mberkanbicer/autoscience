"""Research orchestrator that connects all modules."""

from typing import Any

import asyncio
import structlog
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import create_all_agents
from app.connectors.manager import ConnectorManager
from app.engine.clustering import ClusteringEngine
from app.engine.conflict_detection import ConflictDetectionEngine
from app.engine.hypothesis_generation import HypothesisGenerationEngine
from app.engine.idle_cognition import IdleCognitionEngine
from app.engine.keyword_engine import KeywordExpansionEngine
from app.engine.literature_engine import LiteratureEngine
from app.engine.paper_analysis import PaperAnalysisEngine
from app.engine.question_generation import QuestionGenerationEngine
from app.engine.scoring import IdeaScoringEngine
from app.engine.validation_planning import ValidationPlanningEngine
from app.llm.router import LLMRouter
from app.schemas.research_run import ResearchRunCreate, ResearchRunUpdate
from app.schemas.research_state import ResearchState, RunBudget, RunState, RunType
from app.services.audit_service import AuditService
from app.services.cluster_service import ClusterService
from app.services.conflict_service import ConflictService
from app.services.hypothesis_service import HypothesisService
from app.services.idea_ledger_service import IdeaLedgerService
from app.services.idea_service import IdeaService
from app.services.knowledge_service import KnowledgeBaseService
from app.services.literature_service import LiteratureService
from app.services.paper_analysis_service import PaperAnalysisService
from app.services.paper_service import PaperService
from app.services.project_service import ProjectService
from app.services.question_service import ResearchQuestionService
from app.services.report_generator import ReportGenerator
from app.services.research_persistence_service import ResearchPersistenceService
from app.services.research_run_service import ResearchRunService
from app.services.safety_service import SafetyService
from app.services.scoring_service import IdeaScoringService
from app.services.skill_memory_service import SkillMemoryService
from app.services.skill_performance_service import SkillPerformanceService
from app.services.snapshot_service import SnapshotService
from app.services.validation_service import ValidationPlanService
from app.workflows.research_workflow import (
    ResearchWorkflow,
    WorkflowConfig,
    WorkflowStep,
    deserialize_step_history,
)
from app.workflows.safety_gates import ApprovalGateError, ProjectSafetySettings

logger = structlog.get_logger()


class ResearchOrchestrator:
    """Orchestrator that connects all research modules."""

    def __init__(
        self,
        db: AsyncSession,
        llm_router: LLMRouter,
        connector_manager: ConnectorManager,
        event_broadcaster=None,
    ):
        self.db = db
        self.llm = llm_router
        self.connectors = connector_manager
        self.event_broadcaster = event_broadcaster

        # Initialize engines
        self.keyword_engine = KeywordExpansionEngine(llm_router)
        self.literature_engine = LiteratureEngine(llm_router, connector_manager)
        self.paper_analysis_engine = PaperAnalysisEngine(llm_router)
        self.clustering_engine = ClusteringEngine(llm_router)
        self.conflict_engine = ConflictDetectionEngine(llm_router)
        self.question_engine = QuestionGenerationEngine(llm_router)
        self.hypothesis_engine = HypothesisGenerationEngine(llm_router)
        self.validation_engine = ValidationPlanningEngine(llm_router)
        self.scoring_engine = IdeaScoringEngine(llm_router)
        self.idle_engine = IdleCognitionEngine(llm_router)

        # Initialize services
        self.project_service = ProjectService(db)
        self.idea_service = IdeaService(db)
        self.idea_ledger = IdeaLedgerService(db)
        self.run_service = ResearchRunService(db)
        self.paper_service = PaperService(db)
        self.literature_service = LiteratureService(db)
        self.analysis_service = PaperAnalysisService(db)
        self.cluster_service = ClusterService(db)
        self.conflict_service = ConflictService(db)
        self.question_service = ResearchQuestionService(db)
        self.hypothesis_service = HypothesisService(db)
        self.validation_service = ValidationPlanService(db)
        self.scoring_service = IdeaScoringService(db)
        self.skill_service = SkillMemoryService(db)
        self.knowledge_service = KnowledgeBaseService(db, llm_router)
        self.report_generator = ReportGenerator(db, llm_router)
        self.audit_service = AuditService(db)
        self.safety_service = SafetyService(db)

        # Initialize agents
        self.agents = create_all_agents(llm_router)

    def _build_workflow(
        self,
        run,
        project,
        run_type: str,
        flexibility: float,
    ) -> ResearchWorkflow:
        """Create a workflow wired with project safety settings."""
        self.safety_service.policy.max_cost_per_run = run.max_cost_usd or self.safety_service.policy.max_cost_per_run
        return ResearchWorkflow(
            agents=self.agents,
            config=WorkflowConfig(run_type=run_type, flexibility=flexibility),
            run_id=run.id,
            run_service=self.run_service,
            keyword_engine=self.keyword_engine,
            literature_engine=self.literature_engine,
            analysis_engine=self.paper_analysis_engine,
            clustering_engine=self.clustering_engine,
            conflict_engine=self.conflict_engine,
            question_engine=self.question_engine,
            hypothesis_engine=self.hypothesis_engine,
            validation_engine=self.validation_engine,
            scoring_engine=self.scoring_engine,
            idea_ledger=self.idea_ledger,
            db=self.db,
            event_broadcaster=self.event_broadcaster,
            safety_service=self.safety_service,
            project_safety_settings=ProjectSafetySettings(
                approval_required_for_external_actions=project.approval_required_for_external_actions,
                max_cost_per_run_usd=run.max_cost_usd,
            ),
            knowledge_service=self.knowledge_service,
        )

    async def _finalize_run(
        self,
        project_id: str,
        run_id: str,
        idea_text: str,
        state: ResearchState,
    ) -> None:
        """Generate report, update knowledge base, and log completion."""
        report_content = await self.report_generator.generate_report(state)
        await self.report_generator.save_report(
            project_id=project_id,
            run_id=run_id,
            title=f"Research Report: {idea_text[:100]}",
            content=report_content,
            report_type="cycle",
        )
        await self.knowledge_service.generate_project_summary(project_id)
        await self.audit_service.log_event(
            event_type="research_completed",
            project_id=project_id,
            run_id=run_id,
            details={
                "papers_found": len(state.papers),
                "conflicts_found": len(state.conflicts),
                "questions_generated": len(state.questions),
                "hypotheses_formed": len(state.hypotheses),
            },
        )

        # Run skill performance evaluation after each research cycle
        try:
            perf_service = SkillPerformanceService(self.db)
            perf_result = await perf_service.evaluate_all_skills(project_id=project_id)
            if perf_result.deprecated or perf_result.retired:
                logger.info(
                    "skill_performance_after_run",
                    project_id=project_id,
                    deprecated=len(perf_result.deprecated),
                    retired=len(perf_result.retired),
                    summary=perf_result.summary,
                )
                await self.audit_service.log_event(
                    event_type="skill_performance_evaluation",
                    project_id=project_id,
                    run_id=run_id,
                    details={
                        "deprecated": [r.skill_name for r in perf_result.deprecated],
                        "retired": [r.skill_name for r in perf_result.retired],
                        "summary": perf_result.summary,
                    },
                )
        except SQLAlchemyError as exc:
            logger.warning("skill_performance_evaluation_failed", error=str(exc))
        except Exception as exc:
            logger.warning("skill_performance_evaluation_unexpected", error=str(exc))

    async def run_research(
        self,
        project_id: str,
        idea_text: str,
        run_type: str = "user_directed",
        flexibility: float = 0.6,
        existing_run_id: str | None = None,
    ) -> ResearchState:
        """Run a complete research cycle."""
        logger.info(
            "research_started",
            project_id=project_id,
            run_type=run_type,
        )

        # Explicit transaction wrapper for atomic operations
        async with self.db.begin():
            if existing_run_id:
                run = await self.run_service.get_run(existing_run_id)
                if not run:
                    raise ValueError(f"Run {existing_run_id} not found")
                idea = await self.idea_ledger.get_idea(run.idea_id)
                if not idea:
                    raise ValueError(f"Idea {run.idea_id} not found for run {existing_run_id}")
            else:
                idea = await self.idea_ledger.create_idea(
                    project_id=project_id,
                    text=idea_text,
                    origin="user_prompt",
                    flexibility=flexibility,
                )
                run = await self.run_service.create_run(
                    project_id=project_id,
                    data=ResearchRunCreate(
                        idea_id=idea.id,
                        run_type=run_type,
                    ),
                )

            # Initialize state
            state = ResearchState(
                run_id=run.id,
                project_id=project_id,
                idea_id=idea.id,
                run_type=RunType(run_type),
                original_idea=idea_text,
                current_idea=idea_text,
                flexibility=flexibility,
                budget=RunBudget(),
            )

        project = await self.project_service.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        workflow = self._build_workflow(run, project, run_type, flexibility)

        # Execute research workflow
        try:
            await self.run_service.start_run(run.id)
            state = await workflow.run(state)
            await self._store_results(state)
            await self.run_service.complete_run(run.id)
            await self._safety_check(state)
        except ApprovalGateError as gate_error:
            logger.info(
                "research_waiting_for_approval",
                run_id=run.id,
                approval_id=gate_error.approval_id,
                step=gate_error.step,
            )
            state.state = RunState.WAITING_FOR_APPROVAL
            try:
                await self._store_results(state)
            except (TypeError, ValueError, SQLAlchemyError) as store_error:
                logger.warning("store_results_on_approval_failed", error=str(store_error))
            except Exception as store_error:
                logger.warning("store_results_on_approval_unexpected", error=str(store_error))
            try:
                await self.db.commit()
            except SQLAlchemyError as commit_error:
                logger.warning("commit_failed", error=str(commit_error))
            return state
        except asyncio.CancelledError:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error("research_run_failed", run_id=run.id, error=str(e))
            try:
                await self.run_service.fail_run(run.id, error=str(e))
            except SQLAlchemyError as nested_e:
                logger.error("fail_run_marking_failed", run_id=run.id, error=str(nested_e))
            except Exception as nested_e:
                logger.error("fail_run_marking_unexpected", run_id=run.id, error=str(nested_e))
            raise e

        await self._finalize_run(project_id, run.id, idea_text, state)

        logger.info(
            "research_completed",
            project_id=project_id,
            run_id=run.id,
            papers=len(state.papers),
            hypotheses=len(state.hypotheses),
        )

        try:
            await self.db.commit()
        except SQLAlchemyError as e:
            logger.warning("commit_failed", error=str(e))
            await self.db.rollback()

        return state

    async def resume_research(self, run_id: str) -> ResearchState:
        """Resume a run that was paused for approval."""
        run = await self.run_service.get_run(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        if run.state != "waiting_for_approval":
            raise ValueError(f"Run {run_id} is not waiting for approval (state={run.state})")

        project = await self.project_service.get_project(run.project_id)
        if not project:
            raise ValueError(f"Project {run.project_id} not found")

        snapshot_service = SnapshotService(self.db)
        state = await snapshot_service.create_snapshot(run_id)
        if not state:
            raise ValueError(f"Could not restore state for run {run_id}")

        # If the run was paused because the budget was exhausted, mark the state
        # so the budget hard-cap check in _execute_step is skipped on resume.
        # (The user's explicit approval is the budget extension.)
        if state.is_budget_exceeded():
            state.budget_extension_approved = True
            logger.info("budget_extension_approved_on_resume", run_id=run_id, cost=state.cost_usd)

        try:
            start_step = WorkflowStep(run.current_phase) if run.current_phase else WorkflowStep.RETRIEVE_LITERATURE
        except ValueError:
            start_step = WorkflowStep.RETRIEVE_LITERATURE

        workflow = self._build_workflow(run, project, run.run_type, state.flexibility)
        if run.step_history:
            workflow.step_history = deserialize_step_history(run.step_history)
        idea_text = state.current_idea or state.original_idea

        try:
            await self.run_service.update_run(run_id, ResearchRunUpdate(state="running"))
            state = await workflow.run_from_step(state, start_step)
            await self._store_results(state)
            await self.run_service.complete_run(run_id)
            await self._safety_check(state)
        except ApprovalGateError as gate_error:
            logger.info(
                "research_waiting_for_approval",
                run_id=run_id,
                approval_id=gate_error.approval_id,
                step=gate_error.step,
            )
            state.state = RunState.WAITING_FOR_APPROVAL
            try:
                await self._store_results(state)
            except (TypeError, ValueError, SQLAlchemyError) as store_error:
                logger.warning("store_results_on_approval_failed", error=str(store_error))
            except Exception as store_error:
                logger.warning("store_results_on_approval_unexpected", error=str(store_error))
            await self.db.commit()
            return state
        except asyncio.CancelledError:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error("research_resume_failed", run_id=run_id, error=str(e))
            try:
                await self.run_service.fail_run(run_id, error=str(e))
            except SQLAlchemyError as fail_e:
                logger.error("fail_run_marking_failed", run_id=run_id, error=str(fail_e))
            except Exception as fail_e:
                logger.error("fail_run_marking_unexpected", run_id=run_id, error=str(fail_e))
            raise

        await self._finalize_run(run.project_id, run_id, idea_text, state)
        await self.db.commit()
        return state

    async def _safety_check(self, state: ResearchState) -> None:
        """Validate research state for safety, quality, and cost risks."""
        # 1. Cost Safety
        if state.cost_usd > 10.0:
            logger.warning("safety_risk_detected", reason="high_cost", cost=state.cost_usd)
            state.warnings.append("High research cost ($10+) detected.")

        # 2. Quality / Hallucination check
        if len(state.papers) > 5:
            titles = [p.title.lower().strip() for p in state.papers]
            # If more than 50% of papers have identical titles, it's a loop
            unique_ratio = len(set(titles)) / len(titles)
            if unique_ratio < 0.5:
                logger.warning("quality_risk_detected", reason="potential_hallucination_loop", ratio=unique_ratio)
                state.add_error("quality_risk", "High duplication in search results. Potential LLM loop detected.")

        # 3. Cognitive Health check
        if state.cognitive_entropy < 0.1 and len(state.papers) > 10:
             state.warnings.append("Extremely narrow research focus (Exploitation mode). Consider increasing flexibility.")

    async def _store_results(self, state: ResearchState) -> None:
        """Store research results via the unified persistence service."""
        persistence = ResearchPersistenceService(self.db, self.llm)
        await persistence.persist_run_results(state)

    async def run_idle_cycle(
        self,
        project_id: str,
    ) -> dict[str, Any]:
        """Run an idle cognition cycle."""
        from .idle_cycle_service import IdleCycleService

        project = await self.project_service.get_project(project_id)
        if not project:
            return {"error": "Project not found"}

        result = await self.idle_engine.run_idle_cycle(
            project_id=project_id,
            project_domain=project.domain,
        )

        cycle_service = IdleCycleService(self.db)
        await cycle_service.store_cycle(project_id, result)

        await self.audit_service.log_event(
            event_type="idle_cycle_completed",
            project_id=project_id,
            details={
                "cycle_id": result.cycle_id,
                "mode": result.idle_mode,
                "ideas_generated": result.ideas_generated,
                "questions_generated": result.questions_generated,
            },
        )

        try:
            await self.db.commit()
        except SQLAlchemyError as exc:
            logger.warning("idle_cycle_commit_failed", error=str(exc))

        return {
            "cycle_id": result.cycle_id,
            "mode": result.idle_mode,
            "ideas_generated": result.ideas_generated,
            "questions_generated": result.questions_generated,
            "notes": result.notes,
        }
