"""Research question and hypothesis API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..services.research_question_service import ResearchQuestionService, HypothesisService
from ..schemas.research_question import (
    ResearchQuestionCreate,
    ResearchQuestionResponse,
    HypothesisCreate,
    HypothesisUpdate,
    HypothesisResponse,
    ValidationPlanCreate,
    ValidationPlanResponse,
)

router = APIRouter()


# Research Questions

@router.get("/questions", response_model=list[ResearchQuestionResponse])
async def list_questions(
    project_id: str = Query(...),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List research questions for a project."""
    service = ResearchQuestionService(db)
    questions = await service.list_questions(project_id, status, page, per_page)
    return questions


@router.post("/questions", response_model=ResearchQuestionResponse, status_code=201)
async def create_question(
    project_id: str = Query(...),
    question_in: ResearchQuestionCreate = ...,
    db: AsyncSession = Depends(get_db),
):
    """Create a new research question."""
    service = ResearchQuestionService(db)
    question = await service.create_question(project_id, question_in)
    return question


@router.get("/questions/{question_id}", response_model=ResearchQuestionResponse)
async def get_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a research question."""
    service = ResearchQuestionService(db)
    question = await service.get_question(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.post("/questions/{question_id}/reject", response_model=ResearchQuestionResponse)
async def reject_question(
    question_id: str,
    reason: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Reject a research question."""
    service = ResearchQuestionService(db)
    question = await service.reject_question(question_id, reason)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


# Hypotheses

@router.get("/hypotheses", response_model=list[HypothesisResponse])
async def list_hypotheses(
    project_id: str = Query(...),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List hypotheses for a project."""
    service = HypothesisService(db)
    hypotheses = await service.list_hypotheses(project_id, status, page, per_page)
    return hypotheses


@router.post("/hypotheses", response_model=HypothesisResponse, status_code=201)
async def create_hypothesis(
    project_id: str = Query(...),
    hypothesis_in: HypothesisCreate = ...,
    db: AsyncSession = Depends(get_db),
):
    """Create a new hypothesis."""
    service = HypothesisService(db)
    hypothesis = await service.create_hypothesis(project_id, hypothesis_in)
    return hypothesis


@router.get("/hypotheses/{hypothesis_id}", response_model=HypothesisResponse)
async def get_hypothesis(
    hypothesis_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a hypothesis."""
    service = HypothesisService(db)
    hypothesis = await service.get_hypothesis(hypothesis_id)
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return hypothesis


@router.put("/hypotheses/{hypothesis_id}", response_model=HypothesisResponse)
async def update_hypothesis(
    hypothesis_id: str,
    hypothesis_in: HypothesisUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a hypothesis."""
    service = HypothesisService(db)
    hypothesis = await service.update_hypothesis(hypothesis_id, hypothesis_in)
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return hypothesis


# Validation Plans

@router.get("/hypotheses/{hypothesis_id}/validation", response_model=ValidationPlanResponse | None)
async def get_validation_plan(
    hypothesis_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get validation plan for a hypothesis."""
    service = HypothesisService(db)
    plan = await service.get_validation_plan(hypothesis_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Validation plan not found")
    return plan


@router.post("/hypotheses/{hypothesis_id}/validation", response_model=ValidationPlanResponse, status_code=201)
async def create_validation_plan(
    hypothesis_id: str,
    plan_in: ValidationPlanCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create or update validation plan."""
    service = HypothesisService(db)
    plan_in.hypothesis_id = hypothesis_id
    plan = await service.create_validation_plan(plan_in)
    return plan
