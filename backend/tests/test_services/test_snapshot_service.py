"""Tests for research run snapshot restoration."""

from uuid import uuid4

import pytest

from app.models.idea import Idea, IdeaScore
from app.models.paper import Paper, PaperCluster, ClusterConflict
from app.models.project import Project
from app.models.research_question import Hypothesis, ResearchQuestion
from app.models.research_run import ResearchRun, ResearchRunEvent
from app.models.report import AnalysisArtifact, AnalysisRun
from app.schemas.research_state import RunState
from app.services.snapshot_service import SnapshotService


@pytest.mark.asyncio
async def test_create_snapshot_scopes_run_artifacts_and_restores_metrics(db_session):
    project_id = str(uuid4())
    run_id = str(uuid4())
    idea_id = str(uuid4())
    paper_a_id = str(uuid4())
    paper_b_id = str(uuid4())
    other_run_id = str(uuid4())

    db_session.add(
        Project(
            id=project_id,
            name="Snapshot Test",
            domain="ML",
            default_flexibility=0.6,
            idle_research_enabled=False,
            idle_trigger_minutes=120,
            max_idle_cycles_per_day=3,
            max_sources_per_cycle=50,
            approval_required_for_external_actions=True,
        )
    )
    db_session.add(
        Idea(
            id=idea_id,
            project_id=project_id,
            origin="user_prompt",
            initial_text="Transformer efficiency",
            current_text="Transformer efficiency",
            flexibility=0.7,
            classification="promising",
        )
    )
    db_session.add(
        ResearchRun(
            id=run_id,
            project_id=project_id,
            idea_id=idea_id,
            run_type="user_directed",
            state="waiting_for_approval",
            current_phase="retrieve_literature",
            cognitive_entropy=0.82,
            cognitive_mode="exploration",
            step_history=[{"step": "plan_search", "status": "completed", "duration_seconds": 1.2}],
        )
    )
    db_session.add(
        ResearchRun(
            id=other_run_id,
            project_id=project_id,
            idea_id=idea_id,
            run_type="user_directed",
            state="completed",
        )
    )
    db_session.add_all(
        [
            Paper(id=paper_a_id, project_id=project_id, title="Paper A", authors=["A"], year=2024),
            Paper(id=paper_b_id, project_id=project_id, title="Paper B", authors=["B"], year=2023),
        ]
    )
    db_session.add(
        PaperCluster(
            id=str(uuid4()),
            project_id=project_id,
            run_id=run_id,
            name="Methods",
            cluster_type="method",
            paper_ids=[paper_a_id],
        )
    )
    db_session.add(
        ClusterConflict(
            id=str(uuid4()),
            project_id=project_id,
            run_id=run_id,
            conflict_type="finding",
            description="A conflicts with B",
            supporting_papers=[paper_a_id],
            opposing_papers=[paper_b_id],
            severity=0.7,
        )
    )
    question_id = str(uuid4())
    db_session.add(
        ResearchQuestion(
            id=question_id,
            project_id=project_id,
            run_id=run_id,
            question="Does method X generalize?",
            status="generated",
        )
    )
    db_session.add(
        Hypothesis(
            id=str(uuid4()),
            project_id=project_id,
            idea_id=idea_id,
            question_id=question_id,
            statement="Method X improves accuracy",
            status="draft",
            confidence=0.6,
        )
    )
    db_session.add(
        IdeaScore(
            id=str(uuid4()),
            idea_id=idea_id,
            novelty=0.8,
            feasibility=0.7,
            importance=0.9,
            overall_value=0.82,
            scoring_rationale="Strong evidence",
            cost_usd=1.25,
        )
    )
    db_session.add(
        ResearchRunEvent(
            id=str(uuid4()),
            run_id=run_id,
            event_type="keywords",
            details={"keywords": ["transformer", "efficiency"]},
        )
    )
    analysis_run_id = str(uuid4())
    db_session.add(
        AnalysisRun(
            id=analysis_run_id,
            run_id=run_id,
            script="print('ok')",
            status="completed",
        )
    )
    db_session.add(
        AnalysisArtifact(
            id=str(uuid4()),
            analysis_run_id=analysis_run_id,
            artifact_type="stdout",
            description="ok",
        )
    )
    await db_session.flush()

    snapshot = await SnapshotService(db_session).create_snapshot(run_id)

    assert snapshot is not None
    assert snapshot.state == RunState.WAITING_FOR_APPROVAL
    assert snapshot.current_phase == "retrieve_literature"
    assert snapshot.cognitive_entropy == 0.82
    assert snapshot.cognitive_mode == "exploration"
    assert snapshot.keywords == ["transformer", "efficiency"]
    assert len(snapshot.papers) == 1
    assert snapshot.papers[0].id == paper_a_id
    assert len(snapshot.clusters) == 1
    assert len(snapshot.conflicts) == 1
    assert len(snapshot.questions) == 1
    assert len(snapshot.hypotheses) == 1
    assert snapshot.scores[-1].novelty == 0.8
    assert snapshot.scores[-1].rationale == "Strong evidence"
    assert snapshot.experiment_code == "print('ok')"
    assert snapshot.experiment_result is not None
    assert snapshot.experiment_result["stdout"] == "ok"