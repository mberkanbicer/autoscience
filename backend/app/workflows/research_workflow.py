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
    ):
        self.agents = agents
        self.config = config or WorkflowConfig(run_type="user_directed")
        self.step_history: list[WorkflowStepResult] = []
        self.status = WorkflowStatus.PENDING
        self.run_id = run_id
        self.run_service = run_service
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
        self.scoring_engine = scoring_engine

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

            # Broadcast completion
            if self.event_broadcaster and self.run_id:
                try:
                    await self.event_broadcaster.publish(
                        self.run_id, "run_completed", {
                            "papers": len(state.papers),
                            "conflicts": len(state.conflicts),
                            "questions": len(state.questions),
                            "hypotheses": len(state.hypotheses),
                        }
                    )
                except Exception:
                    pass

        except Exception as e:
            logger.error("workflow_failed", error=str(e))
            self.status = WorkflowStatus.FAILED
            state.state = RunState.FAILED
            state.add_error("workflow_failed", str(e))

            # Broadcast failure
            if self.event_broadcaster and self.run_id:
                try:
                    await self.event_broadcaster.publish(
                        self.run_id, "run_failed", {
                            "error": str(e),
                        }
                    )
                except Exception:
                    pass

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

        # Broadcast step progress
        if self.event_broadcaster and self.run_id:
            try:
                await self.event_broadcaster.publish(
                    self.run_id, "step_started", {
                        "step": step.value,
                        "label": self._phase_label(step),
                    }
                )
            except Exception:
                pass

        try:
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

            # Persist event to DB (best-effort, never crash)
            if self.run_service and self.run_id:
                try:
                    await self.run_service.add_run_event(
                        self.run_id, "step_completed", actor="workflow",
                        details={"step": step.value, "duration": round(duration, 2),
                                 "phase_label": self._phase_label(step)},
                    )
                    agent_role = self._step_to_agent(step)
                    await self.run_service.add_tool_call(
                        run_id=self.run_id,
                        tool_name=f"step_{step.value}",
                        agent_role=agent_role,
                        duration_ms=int(duration * 1000),
                        success=True,
                    )
                except Exception:
                    pass

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
        """Plan literature search — expand keywords and broadcast them."""
        keywords = None
        if self.keyword_engine:
            try:
                kw_result = await self.keyword_engine.expand_keywords(state.current_idea)
                all_terms = []
                all_terms.extend(kw_result.core_concepts)
                all_terms.extend(kw_result.synonyms)
                all_terms.extend(kw_result.method_terms)
                keywords = all_terms if all_terms else None
            except Exception as e:
                logger.warning("keyword_expansion_failed", error=str(e))

        # Store keywords in state for use by _retrieve_literature
        state.keywords = keywords or []

        # Broadcast keywords event
        if self.event_broadcaster and self.run_id:
            try:
                await self.event_broadcaster.publish(
                    self.run_id, "keywords", {
                        "idea": state.current_idea,
                        "keywords": state.keywords,
                    }
                )
            except Exception:
                pass

        state.current_phase = "search_planned"
        return state

    async def _retrieve_literature(self, state: ResearchState) -> ResearchState:
        """Retrieve literature by searching academic databases."""
        from ..schemas.research_state import PaperSummary

        if not self.literature_engine:
            logger.warning("no_literature_engine")
            state.current_phase = "literature_retrieved"
            return state

        # Use keywords from state (expanded in _plan_search)
        keywords = state.keywords if state.keywords else None

        # Broadcast search start
        if self.event_broadcaster and self.run_id:
            try:
                sources = list(self.connectors.connectors.keys()) if self.connectors else []
                await self.event_broadcaster.publish(
                    self.run_id, "search_started", {
                        "sources": sources,
                        "query": " ".join((keywords or [])[:5]),
                        "max_results": min(state.budget.max_sources, 30),
                    }
                )
            except Exception:
                pass

        # Search academic databases
        try:
            result = await self.literature_engine.retrieve_literature(
                idea=state.current_idea,
                keywords=keywords,
                limit=min(state.budget.max_sources, 30),
            )

            # Broadcast results summary
            if self.event_broadcaster and self.run_id:
                try:
                    await self.event_broadcaster.publish(
                        self.run_id, "search_results", {
                            "total_found": result.total_found,
                            "papers_count": len(result.papers),
                            "search_queries": result.search_queries_used,
                        }
                    )
                except Exception:
                    pass

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
                    )
                )

                # Broadcast each paper found
                if self.event_broadcaster and self.run_id:
                    try:
                        await self.event_broadcaster.publish(
                            self.run_id, "paper_found", {
                                "id": paper_id,
                                "title": paper.title,
                                "authors": paper.authors[:3] if isinstance(paper.authors, list) else [],
                                "year": paper.year,
                                "source": paper.source,
                                "doi": paper.doi,
                                "url": paper.url,
                            }
                        )
                    except Exception:
                        pass

            state.sources_searched += result.total_found
            logger.info(
                "literature_retrieved",
                papers_found=len(result.papers),
                total_sources=result.total_found,
            )

        except Exception as e:
            logger.error("literature_retrieval_failed", error=str(e))
            state.add_error("literature_retrieval", str(e))

        # Broadcast completion
        if self.event_broadcaster and self.run_id:
            try:
                await self.event_broadcaster.publish(
                    self.run_id, "search_complete", {
                        "papers_count": len(state.papers),
                    }
                )
            except Exception:
                pass

        state.current_phase = "literature_retrieved"
        return state

    async def _analyze_papers(self, state: ResearchState) -> ResearchState:
        """Analyze papers using the analysis engine."""
        if not self.analysis_engine or not state.papers:
            state.current_phase = "papers_analyzed"
            return state

        try:
            # Analyze up to 10 papers
            for paper_summary in state.papers[:10]:
                try:
                    analysis = await self.analysis_engine.analyze_paper(
                        paper_id=paper_summary.id,
                        title=paper_summary.title,
                        abstract="",  # Would need full paper data
                        idea_context=state.current_idea,
                    )
                    if analysis:
                        # Store analysis in DB
                        try:
                            from ..models.paper import PaperAnalysis as PaperAnalysisModel
                            from uuid import uuid4
                            db_analysis = PaperAnalysisModel(
                                id=str(uuid4()),
                                paper_id=paper_summary.id,
                                problem=analysis.problem,
                                method=analysis.method,
                                metrics=analysis.metrics,
                                findings=analysis.findings,
                                limitations=analysis.limitations,
                                confidence=analysis.confidence,
                            )
                            self.db.add(db_analysis)
                        except Exception:
                            pass
                        state.add_event("paper_analyzed", details={"paper": paper_summary.title[:80]})
                except Exception as e:
                    logger.warning("paper_analysis_failed", paper=paper_summary.title[:50], error=str(e))

            state.add_event("papers_analyzed", details={"count": min(len(state.papers), 10)})
        except Exception as e:
            logger.error("analysis_failed", error=str(e))

        state.current_phase = "papers_analyzed"
        return state

    async def _cluster_papers(self, state: ResearchState) -> ResearchState:
        """Cluster papers using the clustering engine."""
        from ..schemas.research_state import ClusterSummary

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
            if result and hasattr(result, 'clusters'):
                for c in result.clusters[:10]:
                    state.clusters.append(
                        ClusterSummary(
                            id=c.id,
                            name=c.name,
                            description=c.description,
                            paper_count=len(c.paper_ids),
                        )
                    )
            state.add_event("papers_clustered", details={"clusters": len(state.clusters)})
        except Exception as e:
            logger.error("clustering_failed", error=str(e))

        state.current_phase = "papers_clustered"
        return state

    async def _detect_conflicts(self, state: ResearchState) -> ResearchState:
        """Detect conflicts using the conflict engine."""
        from ..schemas.research_state import ConflictSummary

        if not self.conflict_engine or len(state.papers) < 2:
            state.current_phase = "conflicts_detected"
            return state

        try:
            paper_dicts = [
                {"title": p.title, "authors": p.authors, "year": p.year, "id": p.id}
                for p in state.papers[:15]
            ]
            result = await self.conflict_engine.detect_conflicts(papers=paper_dicts)
            if result and hasattr(result, 'conflicts'):
                for c in result.conflicts[:10]:
                    state.conflicts.append(
                        ConflictSummary(
                            id=c.id,
                            conflict_type=c.conflict_type,
                            description=c.description,
                            severity=c.severity,
                        )
                    )
        except Exception as e:
            logger.error("conflict_detection_failed", error=str(e))

        state.current_phase = "conflicts_detected"
        return state

    async def _generate_questions(self, state: ResearchState) -> ResearchState:
        """Generate research questions using the question engine."""
        from ..schemas.research_state import QuestionSummary
        from ..engine.conflict_detection import Conflict, Gap

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
            if result and hasattr(result, 'questions'):
                for q in result.questions[:10]:
                    state.questions.append(
                        QuestionSummary(
                            id=q.id,
                            question=q.question,
                            rank=q.overall_score,
                            status="active",
                        )
                    )
        except Exception as e:
            logger.error("question_generation_failed", error=str(e))

        state.current_phase = "questions_generated"
        return state

    async def _form_hypotheses(self, state: ResearchState) -> ResearchState:
        """Form hypotheses using the hypothesis engine."""
        from ..schemas.research_state import HypothesisSummary

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
            if result and hasattr(result, 'hypotheses'):
                for h in result.hypotheses:
                    state.hypotheses.append(
                        HypothesisSummary(
                            id=h.id if hasattr(h, 'id') else '',
                            statement=h.statement if hasattr(h, 'statement') else str(h),
                            confidence=h.confidence if hasattr(h, 'confidence') else 0.5,
                            status="draft",
                        )
                    )
        except Exception as e:
            logger.error("hypothesis_generation_failed", error=str(e))

        state.current_phase = "hypotheses_formed"

        # Capture sub-ideas from promising hypotheses
        await self._capture_sub_ideas(state)

        return state

    async def _capture_sub_ideas(self, state: ResearchState):
        """Capture sub-ideas from hypotheses and questions that suggest new directions."""
        if not state.hypotheses or not state.idea_id:
            return

        try:
            from ..services.idea_ledger_service import IdeaLedgerService
            from ..models.idea import Idea as IdeaModel
            from sqlalchemy import select

            idea_ledger = IdeaLedgerService(self.db)

            # Find high-confidence hypotheses that suggest new research directions
            for hyp in state.hypotheses:
                if hyp.confidence and hyp.confidence >= 0.6:
                    # Check if this hypothesis already generated a sub-idea
                    existing = await self.db.execute(
                        select(IdeaModel).where(
                            IdeaModel.parent_idea_id == state.idea_id,
                            IdeaModel.current_text.like(f"%{hyp.statement[:50]}%")
                        ).limit(1)
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
                        __import__('sqlalchemy').update(IdeaModel)
                        .where(IdeaModel.id == sub_idea.id)
                        .values(parent_idea_id=state.idea_id)
                    )
                    state.add_event("sub_idea_captured", details={
                        "sub_idea_id": sub_idea.id,
                        "parent_idea_id": state.idea_id,
                        "hypothesis": hyp.statement[:100],
                    })
                    logger.info("sub_idea_captured", sub_idea_id=sub_idea.id, hypothesis=hyp.statement[:80])
        except Exception as e:
            logger.warning("sub_idea_capture_failed", error=str(e))

    async def _plan_validation(self, state: ResearchState) -> ResearchState:
        """Plan validation using the validation engine."""
        if not self.validation_engine or not state.hypotheses:
            state.current_phase = "validation_planned"
            return state

        try:
            hyp_dicts = [
                {"statement": h.statement, "confidence": h.confidence}
                for h in state.hypotheses
            ]
            for h in state.hypotheses[:5]:
                try:
                    await self.validation_engine.create_validation_plan(
                        hypothesis={"statement": h.statement},
                        idea=state.current_idea,
                    )
                    state.add_event("validation_planned", details={"hypothesis": h.statement[:80]})
                except Exception as e:
                    logger.warning("validation_plan_failed", error=str(e))
        except Exception as e:
            logger.error("validation_planning_failed", error=str(e))

        state.current_phase = "validation_planned"
        return state

    async def _score_idea(self, state: ResearchState) -> ResearchState:
        """Score the idea using the scoring engine."""
        from ..schemas.research_state import ScoreSummary

        if not self.scoring_engine:
            state.current_phase = "idea_scored"
            return state

        try:
            # Build paper and conflict dicts for scoring
            paper_dicts = [{"title": p.title, "year": p.year} for p in state.papers]
            conflict_dicts = [{"type": c.conflict_type, "description": c.description} for c in state.conflicts]

            score_result = await self.scoring_engine.score_idea(
                idea={"id": state.idea_id or "", "current_text": state.current_idea},
                papers=paper_dicts if paper_dicts else None,
                conflicts=conflict_dicts if conflict_dicts else None,
            )
            if score_result:
                state.scores.append(
                    ScoreSummary(
                        id=getattr(score_result, 'id', ''),
                        overall_value=getattr(score_result, 'overall_value', None),
                        classification=getattr(score_result, 'classification', None),
                    )
                )
                state.current_classification = getattr(score_result, 'classification', None)
        except Exception as e:
            logger.error("scoring_failed", error=str(e))

        state.current_phase = "idea_scored"
        return state

    async def _make_decision(self, state: ResearchState) -> ResearchState:
        """Make decision on next action and store it."""
        try:
            classification = state.current_classification or "pending"
            # Map classification to valid decision type
            decision_map = {
                'strong': 'promote', 'promising': 'continue', 'moderate': 'continue',
                'weak': 'revise', 'poor': 'archive', 'pending': 'continue',
            }
            decision_type = decision_map.get(classification, 'continue')
            if self.idea_ledger:
                await self.idea_ledger.add_decision(
                    idea_id=state.idea_id,
                    decision=decision_type,
                    reason=f"{len(state.papers)} papers, {len(state.questions)} questions, {len(state.hypotheses)} hypotheses. Classification: {classification}",
                    run_id=state.run_id,
                )
            state.add_event("decision_recorded", details={"classification": classification, "decision": decision_type})
        except Exception as e:
            logger.warning("decision_recording_failed", error=str(e))

        state.current_phase = "decision_made"
        return state

    async def _create_skills(self, state: ResearchState) -> ResearchState:
        """Create skills from successful patterns."""
        try:
            from ..models.skill import Skill as SkillModel
            from uuid import uuid4
            
            # Create a skill based on the research context
            steps_completed = [s.step.value for s in self.step_history if s.status == 'completed']
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
            logger.warning("skill_creation_failed", error=str(e))

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
            WorkflowStep.CREATE_SKILLS: "Creating reusable research skills",
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
            WorkflowStep.CREATE_SKILLS: "skill_curator",
            WorkflowStep.GENERATE_REPORT: "archivist",
        }
        return mapping.get(step, "workflow")
