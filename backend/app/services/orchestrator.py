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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        existing_run_id: str | None = None,
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

        # Use existing run or create new one
        if existing_run_id:
            run = await self.run_service.get_run(existing_run_id)
            if not run:
                raise ValueError(f"Run {existing_run_id} not found")
        else:
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
        )

        state = await workflow.run(state)

        # Store results
        await self._store_results(state)

        # Ensure run is marked as completed (prevents stuck runs)
        try:
            await self.run_service.complete_run(run.id)
        except Exception as e:
            logger.warning("complete_run_failed", run_id=run.id, error=str(e))

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

        # Commit all changes to DB
        try:
            await self.db.commit()
        except Exception as e:
            logger.warning("commit_failed", error=str(e))
            await self.db.rollback()

        return state

    async def _store_results(self, state: ResearchState) -> None:
        """Store research results in the database.

        Writes directly to DB models to avoid service-layer interface mismatches.
        All operations are wrapped in try/except so one failure doesn't block others.
        """
        from uuid import uuid4
        from ..models.paper import Paper, PaperCluster, ClusterLabel, ClusterConflict
        from ..models.research_question import ResearchQuestion, Hypothesis
        from ..models.idea import IdeaScore

        stored = {"papers": 0, "clusters": 0, "conflicts": 0, "questions": 0, "hypotheses": 0, "scores": 0}

        def safe(obj, field, default=None):
            """Safely get attribute from Pydantic model or dict."""
            try:
                if hasattr(obj, 'model_fields') and field in obj.model_fields:
                    return getattr(obj, field, default)
                elif hasattr(obj, field):
                    return getattr(obj, field)
                return default
            except Exception:
                return default

        # --- Papers ---
        # Deduplicate: fetch existing titles for this project
        existing_titles_result = await self.db.execute(
            select(Paper.title).where(Paper.project_id == state.project_id)
        )
        existing_paper_titles = set(t.strip().lower() for t in existing_titles_result.scalars().all())

        for paper in state.papers:
            try:
                normalized_title = paper.title.strip().lower()
                if normalized_title in existing_paper_titles:
                    logger.info("skip_duplicate_paper", title=paper.title[:50])
                    continue
                db_paper = Paper(
                    id=str(uuid4()),
                    project_id=state.project_id,
                    title=paper.title,
                    authors=paper.authors if isinstance(paper.authors, list) else [str(paper.authors)],
                    year=paper.year,
                    doi=paper.doi,
                    abstract=safe(paper, 'abstract'),
                    venue=safe(paper, 'venue'),
                    citation_count=paper.citation_count,
                    paper_type=paper.paper_type,
                )
                self.db.add(db_paper)
                existing_paper_titles.add(normalized_title)
                stored["papers"] += 1
            except Exception as e:
                logger.warning("store_paper_failed", title=paper.title[:50], error=str(e))

        # --- Clusters ---
        for cluster in state.clusters:
            try:
                db_cluster = PaperCluster(
                    id=cluster.id or str(uuid4()),
                    project_id=state.project_id,
                    name=cluster.name,
                    description=cluster.description,
                    cluster_type='topic',
                    paper_ids=[],
                )
                self.db.add(db_cluster)
                stored["clusters"] += 1
            except Exception as e:
                logger.warning("store_cluster_failed", error=str(e))

        # --- Conflicts ---
        for conflict in state.conflicts:
            try:
                db_conflict = ClusterConflict(
                    id=conflict.id or str(uuid4()),
                    project_id=state.project_id,
                    conflict_type=conflict.conflict_type,
                    description=conflict.description,
                    severity=conflict.severity or 0.5,
                    research_opportunity=f'Investigate {conflict.conflict_type} conflict',
                )
                self.db.add(db_conflict)
                stored["conflicts"] += 1
            except Exception as e:
                logger.warning("store_conflict_failed", error=str(e))

        # --- Questions ---
        # Deduplicate: fetch existing question texts for this project
        existing_q_result = await self.db.execute(
            select(ResearchQuestion.question).where(ResearchQuestion.project_id == state.project_id)
        )
        existing_question_texts = set(q.strip().lower() for q in existing_q_result.scalars().all())

        for question in state.questions:
            try:
                normalized_q = question.question.strip().lower()
                if normalized_q in existing_question_texts:
                    logger.info("skip_duplicate_question", question=question.question[:50])
                    continue
                db_question = ResearchQuestion(
                    id=question.id or str(uuid4()),
                    project_id=state.project_id,
                    run_id=state.run_id,
                    idea_id=state.idea_id,
                    question=question.question,
                    rank=question.rank,
                    status="generated",
                )
                self.db.add(db_question)
                existing_question_texts.add(normalized_q)
                stored["questions"] += 1
            except Exception as e:
                logger.warning("store_question_failed", error=str(e))

        # --- Hypotheses ---
        # Deduplicate: fetch existing hypothesis statements for this project
        existing_h_result = await self.db.execute(
            select(Hypothesis.statement).where(Hypothesis.project_id == state.project_id)
        )
        existing_hypothesis_stmts = set(s.strip().lower() for s in existing_h_result.scalars().all())

        for hypothesis in state.hypotheses:
            try:
                normalized_stmt = hypothesis.statement.strip().lower()
                if normalized_stmt in existing_hypothesis_stmts:
                    logger.info("skip_duplicate_hypothesis", statement=hypothesis.statement[:50])
                    continue
                db_hypothesis = Hypothesis(
                    id=hypothesis.id or str(uuid4()),
                    project_id=state.project_id,
                    idea_id=state.idea_id,
                    statement=hypothesis.statement,
                    confidence=hypothesis.confidence,
                    version=1,
                    status="draft",
                )
                self.db.add(db_hypothesis)
                existing_hypothesis_stmts.add(normalized_stmt)
                stored["hypotheses"] += 1
            except Exception as e:
                logger.warning("store_hypothesis_failed", error=str(e))

        # --- Score ---
        if state.scores and state.idea_id:
            try:
                score = state.scores[0]
                db_score = IdeaScore(
                    id=str(uuid4()),
                    idea_id=state.idea_id,
                    overall_value=safe(score, 'overall_value'),
                    scoring_rationale='Auto-scored during research workflow',
                )
                self.db.add(db_score)
                stored["scores"] += 1
            except Exception as e:
                logger.warning("store_score_failed", error=str(e))

        # Commit all stored records
        await self.db.flush()
        logger.info("store_results_done", stored=stored)

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
