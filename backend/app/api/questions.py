"""Research question and hypothesis API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.dependencies.auth import get_current_user, require_project_role
from app.models.collaboration import User
from app.models.research_question import Hypothesis, ResearchQuestion
from app.schemas.research_question import (
    HypothesisCreate,
    HypothesisResponse,
    HypothesisUpdate,
    ResearchQuestionCreate,
    ResearchQuestionResponse,
    ValidationPlanCreate,
    ValidationPlanResponse,
)
from app.services.research_question_service import HypothesisService, ResearchQuestionService

router = APIRouter()


# Research Questions

@router.get("/questions", response_model=list[ResearchQuestionResponse])
async def list_questions(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    project_id: Annotated[str, Query()],
    status: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List research questions for a project."""
    await require_project_role(db, project_id, user.id, "viewer")
    service = ResearchQuestionService(db)
    questions = await service.list_questions(project_id, status, page, per_page)
    return questions


@router.post("/questions", response_model=ResearchQuestionResponse, status_code=201)
async def create_question(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    project_id: Annotated[str, Query()],
    question_in: ResearchQuestionCreate = ...,
):
    """Create a new research question."""
    await require_project_role(db, project_id, user.id, "editor")
    service = ResearchQuestionService(db)
    question = await service.create_question(project_id, question_in)
    return question


@router.get("/questions/{question_id}", response_model=ResearchQuestionResponse)
async def get_question(
    question_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get a research question."""
    question = await db.get(ResearchQuestion, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    await require_project_role(db, question.project_id, user.id, "viewer")

    service = ResearchQuestionService(db)
    return await service.get_question(question_id)


@router.post("/questions/{question_id}/reject", response_model=ResearchQuestionResponse)
async def reject_question(
    question_id: str,
    reason: Annotated[str, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Reject a research question."""
    question = await db.get(ResearchQuestion, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    await require_project_role(db, question.project_id, user.id, "editor")

    service = ResearchQuestionService(db)
    rejected = await service.reject_question(question_id, reason)
    if not rejected:
        raise HTTPException(status_code=404, detail="Question not found")
    return rejected


# Hypotheses

@router.get("/hypotheses", response_model=list[HypothesisResponse])
async def list_hypotheses(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    project_id: Annotated[str, Query()],
    status: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List hypotheses for a project."""
    await require_project_role(db, project_id, user.id, "viewer")
    service = HypothesisService(db)
    hypotheses = await service.list_hypotheses(project_id, status, page, per_page)
    return hypotheses


@router.post("/hypotheses", response_model=HypothesisResponse, status_code=201)
async def create_hypothesis(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    project_id: Annotated[str, Query()],
    hypothesis_in: HypothesisCreate = ...,
):
    """Create a new hypothesis."""
    await require_project_role(db, project_id, user.id, "editor")
    service = HypothesisService(db)
    hypothesis = await service.create_hypothesis(project_id, hypothesis_in)
    return hypothesis


@router.get("/hypotheses/{hypothesis_id}", response_model=HypothesisResponse)
async def get_hypothesis(
    hypothesis_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get a hypothesis."""
    hypothesis = await db.get(Hypothesis, hypothesis_id)
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    await require_project_role(db, hypothesis.project_id, user.id, "viewer")

    service = HypothesisService(db)
    return await service.get_hypothesis(hypothesis_id)


@router.put("/hypotheses/{hypothesis_id}", response_model=HypothesisResponse)
async def update_hypothesis(
    hypothesis_id: str,
    hypothesis_in: HypothesisUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Update a hypothesis."""
    hypothesis = await db.get(Hypothesis, hypothesis_id)
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    await require_project_role(db, hypothesis.project_id, user.id, "editor")

    service = HypothesisService(db)
    updated = await service.update_hypothesis(hypothesis_id, hypothesis_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return updated


# Validation Plans

@router.get("/hypotheses/{hypothesis_id}/validation", response_model=ValidationPlanResponse | None)
async def get_validation_plan(
    hypothesis_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get validation plan for a hypothesis."""
    hypothesis = await db.get(Hypothesis, hypothesis_id)
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    await require_project_role(db, hypothesis.project_id, user.id, "viewer")

    service = HypothesisService(db)
    plan = await service.get_validation_plan(hypothesis_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Validation plan not found")
    return plan


@router.post("/hypotheses/{hypothesis_id}/validation", response_model=ValidationPlanResponse, status_code=201)
async def create_validation_plan(
    hypothesis_id: str,
    plan_in: ValidationPlanCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Create or update validation plan."""
    hypothesis = await db.get(Hypothesis, hypothesis_id)
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    await require_project_role(db, hypothesis.project_id, user.id, "editor")

    service = HypothesisService(db)
    plan_in.hypothesis_id = hypothesis_id
    plan = await service.create_validation_plan(plan_in)
    return plan


@router.post("/hypotheses/{hypothesis_id}/generate-script", response_model=dict)
async def generate_sandbox_script(
    hypothesis_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Generate a sandbox validation script from hypothesis validation plan."""
    from app.engine.sandbox_generator import get_sandbox_generator
    from app.models.research_question import ValidationPlan

    hypothesis = await db.get(Hypothesis, hypothesis_id)
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    await require_project_role(db, hypothesis.project_id, user.id, "editor")

    plan_result = await db.execute(
        select(ValidationPlan).where(ValidationPlan.hypothesis_id == hypothesis_id),
    )
    plan = plan_result.scalar_one_or_none()

    generator = get_sandbox_generator()
    script_data = await generator.generate_script(
        hypothesis_id=hypothesis_id,
        hypothesis_statement=hypothesis.statement,
        validation_plan=plan.model_dump() if plan else {},
    )

    return script_data
