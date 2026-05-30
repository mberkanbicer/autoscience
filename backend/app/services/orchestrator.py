"""Research orchestrator that connects all modules."""

from typing import Any
from datetime import datetime

import structlog

from ..schemas.research_state import ResearchState, RunType, RunState, RunBudget
from ..llm.router import LLMRouter
from ..connectors.manager import ConnectorManager
from ..engine.keyword_engine import KeywordExpansionEngine
from ..engine.literature_engine import LiteratureEngine
from ..engine.paper_analysis import PaperAnalysisEngine
from ..engine.clustering import ClusteringEngine
from ..engine.conflict_detection import ConflictDetectionEngine
from ..engine.question_generation import QuestionGenerationEngine
from ..engine.hypothesis_generation import HypothesisGenerationEngine
from ..engine.validation_planning import ValidationPlanningEngine
from ..engine.scoring import IdeaScoringEngine
from ..engine.idle_cognition import IdleCognitionEngine
from ..workflows.research_workflow import ResearchWorkflow, WorkflowConfig
from ..agents.base import create_all_agents, AgentRole
from ..services.project_service import ProjectService
from ..services.idea_service import IdeaService
from ..services.idea_ledger_service import IdeaLedgerService
from ..services.research_run_service import ResearchRunService
from ..schemas.research_run import ResearchRunCreate
from ..services.paper_service import PaperService
from ..services.literature_service import LiteratureService
from ..services.paper_analysis_service import PaperAnalysisService
from ..services.cluster_service import ClusterService
from ..services.conflict_service import ConflictService
from ..services.question_service import ResearchQuestionService
from ..services.hypothesis_service import HypothesisService
from ..services.validation_service import ValidationPlanService
from ..services.scoring_service import IdeaScoringService
from ..services.skill_memory_service import SkillMemoryService
from ..services.knowledge_service import KnowledgeBaseService
from ..services.report_generator import ReportGenerator
from ..services.audit_service import AuditService
from ..services.safety_service import SafetyService
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ResearchOrchestrator:
    """Orchestrator that connects all research modules."""

    def __init__(
        self,
        db: AsyncSession,
        llm_router: LLMRouter,
        connector_manager: ConnectorManager,
    ):
        self.db = db
        self.llm = llm_router
        self.connectors = connector_manager

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
        self.report_generator = ReportGenerator(db)
        self.audit_service = AuditService(db)
        self.safety_service = SafetyService(db)

        # Initialize agents
        self.agents = create_all_agents(llm_router)

    async def run_research(
        self,
        project_id: str,
        idea_text: str,
        run_type: str = "user_directed",
        flexibility: float = 0.6,
    ) -> ResearchState:
        """Run a complete research cycle."""
        logger.info(
            "research_started",
            project_id=project_id,
            run_type=run_type,
        )

        # Create or get idea
        idea = await self.idea_ledger.create_idea(
            project_id=project_id,
            text=idea_text,
            origin="user_prompt",
            flexibility=flexibility,
        )

        # Create research run
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

        # Start run
        await self.run_service.start_run(run.id)

        # Create and run workflow
        workflow = ResearchWorkflow(
            agents=self.agents,
            config=WorkflowConfig(run_type=run_type, flexibility=flexibility),
            run_id=run.id,
            run_service=self.run_service,
        )

        state = await workflow.run(state)

        # Store results
        await self._store_results(state)

        # Generate report
        report_content = await self.report_generator.generate_report(state)
        await self.report_generator.save_report(
            project_id=project_id,
            run_id=run.id,
            title=f"Research Report: {idea_text[:100]}",
            content=report_content,
            report_type="cycle",
        )

        # Update knowledge base
        await self.knowledge_service.generate_project_summary(project_id)

        # Log completion
        await self.audit_service.log_event(
            event_type="research_completed",
            project_id=project_id,
            run_id=run.id,
            details={
                "papers_found": len(state.papers),
                "conflicts_found": len(state.conflicts),
                "questions_generated": len(state.questions),
                "hypotheses_formed": len(state.hypotheses),
            },
        )

        logger.info(
            "research_completed",
            project_id=project_id,
            run_id=run.id,
            papers=len(state.papers),
            hypotheses=len(state.hypotheses),
        )

        return state

    async def _store_results(self, state: ResearchState) -> None:
        """Store research results in the database."""
        # Store papers
        for paper in state.papers:
            await self.paper_service.create_paper(
                project_id=state.project_id,
                data={
                    "title": paper.title,
                    "authors": paper.authors,
                    "year": paper.year,
                    "doi": paper.doi,
                    "abstract": paper.abstract,
                    "venue": paper.venue,
                    "citation_count": paper.citation_count,
                    "paper_type": paper.paper_type,
                },
            )

        # Store clusters
        for cluster in state.clusters:
            await self.cluster_service.store_clusters(
                project_id=state.project_id,
                clusters=[cluster],
            )

        # Store conflicts
        for conflict in state.conflicts:
            await self.conflict_service.store_conflicts(
                project_id=state.project_id,
                result={"conflicts": [conflict]},
            )

        # Store questions
        for question in state.questions:
            await self.question_service.store_questions(
                project_id=state.project_id,
                result={"questions": [question]},
                run_id=state.run_id,
                idea_id=state.idea_id,
            )

        # Store hypotheses
        for hypothesis in state.hypotheses:
            await self.hypothesis_service.store_hypotheses(
                project_id=state.project_id,
                result={"hypotheses": [hypothesis]},
                idea_id=state.idea_id,
            )

        # Store score
        if state.scores:
            score = state.scores[0]
            await self.scoring_service.store_score(score)

    async def run_idle_cycle(
        self,
        project_id: str,
    ) -> dict[str, Any]:
        """Run an idle cognition cycle."""
        # Get project
        project = await self.project_service.get_project(project_id)
        if not project:
            return {"error": "Project not found"}

        # Run idle cycle
        result = await self.idle_engine.run_idle_cycle(
            project_id=project_id,
            project_domain=project.domain,
        )

        # Log cycle
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

        return {
            "cycle_id": result.cycle_id,
            "mode": result.idle_mode,
            "ideas_generated": result.ideas_generated,
            "questions_generated": result.questions_generated,
            "notes": result.notes,
        }
