"""Idea API endpoints."""

import httpx
import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select as sql_select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

from typing import Annotated

from app.dependencies import get_db
from app.dependencies.auth import get_current_user, require_project_role
from app.models.collaboration import User
from app.schemas.idea import (
    IdeaCreate,
    IdeaDecisionResponse,
    IdeaDetailResponse,
    IdeaResponse,
    IdeaUpdate,
    IdeaVersionResponse,
)
from app.services.idea_service import IdeaService
from app.services.research_run_service import ResearchRunService

router = APIRouter()


@router.get("", response_model=list[IdeaResponse])
async def list_ideas(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Annotated[str, Query()],
    status: Annotated[str | None, Query()] = None,
    classification: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List ideas for a project."""
    service = IdeaService(db)
    ideas = await service.list_ideas(
        project_id=project_id,
        status=status,
        classification=classification,
        page=page,
        per_page=per_page,
    )
    return ideas


@router.post("", response_model=IdeaResponse, status_code=201)
async def create_idea(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    project_id: Annotated[str, Query()],
    idea_in: IdeaCreate = ...,
):
    """Create a new idea."""
    await require_project_role(db, project_id, user.id, "editor")
    service = IdeaService(db)
    idea = await service.create_idea(project_id=project_id, data=idea_in)
    return idea


@router.get("/{idea_id}", response_model=IdeaDetailResponse)
async def get_idea(
    idea_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get idea details."""
    service = IdeaService(db)
    idea = await service.get_idea(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    versions = await service.get_idea_versions(idea_id)
    scores = await service.get_idea_scores(idea_id)
    decisions = await service.get_idea_decisions(idea_id)

    return IdeaDetailResponse(
        id=idea.id,
        created_at=idea.created_at,
        updated_at=idea.updated_at,
        project_id=idea.project_id,
        origin=idea.origin,
        initial_text=idea.initial_text,
        current_text=idea.current_text,
        flexibility=idea.flexibility,
        status=idea.status,
        classification=idea.classification,
        overall_score=idea.overall_score,
        classification_reason=idea.classification_reason,
        scores=scores,
        versions=versions,
        decisions=decisions,
    )


@router.put("/{idea_id}", response_model=IdeaResponse)
async def update_idea(
    idea_id: str,
    idea_in: IdeaUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Update an idea."""
    service = IdeaService(db)
    existing = await service.get_idea(idea_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Idea not found")
    await require_project_role(db, existing.project_id, user.id, "editor")
    idea = await service.update_idea(idea_id, data=idea_in)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    return idea


@router.post("/{idea_id}/pause", response_model=IdeaResponse)
async def pause_idea(
    idea_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Pause an active idea and cancel any running research."""
    service = IdeaService(db)
    idea = await service.get_idea(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    await require_project_role(db, idea.project_id, user.id, "editor")
    if idea.status != "active":
        raise HTTPException(status_code=400, detail=f"Cannot pause idea in '{idea.status}' status")

    # Cancel any running research for this idea
    from sqlalchemy import select as sql_select

    from app.models.research_run import ResearchRun
    result = await db.execute(
        sql_select(ResearchRun).where(
            ResearchRun.idea_id == idea_id,
            ResearchRun.state.in_(["running", "created"]),
        ),
    )
    running_runs = list(result.scalars().all())
    run_service = ResearchRunService(db)
    for run in running_runs:
        await run_service.cancel_run(run.id)

    idea.status = "paused"
    await service.add_idea_decision(idea_id, "pause", f"Paused by user. Cancelled {len(running_runs)} running research.")
    await db.flush()
    await db.refresh(idea)
    return idea


@router.post("/{idea_id}/resume", response_model=IdeaResponse)
async def resume_idea(
    idea_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Resume a paused idea."""
    service = IdeaService(db)
    idea = await service.get_idea(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    await require_project_role(db, idea.project_id, user.id, "editor")
    if idea.status != "paused":
        raise HTTPException(status_code=400, detail=f"Cannot resume idea in '{idea.status}' status")
    idea.status = "active"
    await service.add_idea_decision(idea_id, "resume", "Resumed by user")
    await db.flush()
    await db.refresh(idea)
    return idea


@router.delete("/{idea_id}", status_code=204)
async def delete_idea(
    idea_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Delete an idea."""
    from app.models.idea import Idea as IdeaModel
    from app.services.audit_service import AuditService

    result = await db.execute(sql_select(IdeaModel).where(IdeaModel.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    await require_project_role(db, idea.project_id, user.id, "editor")

    service = IdeaService(db)
    await service.delete_idea(idea_id)

    # Log the deletion
    audit = AuditService(db)
    await audit.log_event(
        event_type="idea_deleted",
        project_id=idea.project_id,
        actor="user",
        action=f"Deleted idea {idea_id}",
    )
    await db.commit()


@router.post("/generate")
async def generate_ideas_from_literature(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Annotated[str, Query()],
    topic: Annotated[str, Query(min_length=5, description="Research topic or field to explore")],
    num_ideas: Annotated[int, Query(ge=1, le=10, description="Number of ideas to generate")] = 5,
    x_openrouter_api_key: Annotated[str | None, Header()] = None,
    x_openrouter_model: Annotated[str | None, Header()] = None,
    x_openai_api_key: Annotated[str | None, Header()] = None,
    x_openai_model: Annotated[str | None, Header()] = None,
    x_anthropic_api_key: Annotated[str | None, Header()] = None,
    x_anthropic_model: Annotated[str | None, Header()] = None,
    x_default_provider: Annotated[str | None, Header()] = None,
):
    """Generate research ideas by analyzing recent literature on a topic."""
    from app.llm.base import Message
    from app.llm.router import LLMRouter
    from app.services.idea_ledger_service import IdeaLedgerService

    # Build LLM router from headers (same as research endpoint)
    llm_router = LLMRouter()
    if x_openrouter_api_key:
        from app.llm.openrouter_provider import OpenRouterProvider
        llm_router.providers["openrouter"] = OpenRouterProvider(
            api_key=x_openrouter_api_key,
            default_model=x_openrouter_model or "openai/gpt-4o",
        )
        llm_router.default_provider = "openrouter"
    elif x_openai_api_key:
        from app.llm.openai_provider import OpenAIProvider
        llm_router.providers["openai"] = OpenAIProvider(
            api_key=x_openai_api_key,
            default_model=x_openai_model or "gpt-4o",
        )
        llm_router.default_provider = "openai"
    elif x_anthropic_api_key:
        from app.llm.anthropic_provider import AnthropicProvider
        llm_router.providers["anthropic"] = AnthropicProvider(
            api_key=x_anthropic_api_key,
            default_model=x_anthropic_model or "claude-sonnet-4-20250514",
        )
        llm_router.default_provider = "anthropic"

    if not llm_router.has_provider():
        raise HTTPException(
            status_code=400,
            detail="No LLM provider configured. Set an API key in Settings first.",
        )

    # Step 1: Search literature
    from app.config import get_settings
    from app.connectors.base import SearchQuery
    from app.connectors.manager import create_default_manager

    settings = get_settings()
    manager = create_default_manager(
        searxng_url=settings.searxng_url,
        firecrawl_api_key=settings.firecrawl_api_key,
    )

    search_query = SearchQuery(text=topic, limit=20)
    all_papers = []
    try:
        # Search SearXNG
        if "searxng" in manager.connectors:
            result = await manager.connectors["searxng"].search(
                query=search_query,
                categories=["science"],
            )
            all_papers.extend(result.papers)
    except httpx.RequestError as e:
        logger.warning("searxng_search_network_error", error=str(e))
    except Exception as e:
        logger.warning("searxng_search_failed", error=str(e))

    try:
        # Also search OpenAlex
        if "openalex" in manager.connectors:
            result = await manager.connectors["openalex"].search(search_query)
            all_papers.extend(result.papers)
    except httpx.RequestError as e:
        logger.warning("openalex_search_network_error", error=str(e))
    except Exception as e:
        logger.warning("openalex_search_failed", error=str(e))

    if not all_papers:
        raise HTTPException(
            status_code=404,
            detail=f"No papers found for topic: {topic}",
        )

    # Deduplicate by title
    seen_titles = set()
    unique_papers = []
    for p in all_papers:
        title_key = (p.title or "").lower().strip()[:80]
        if title_key and title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_papers.append(p)

    # Step 2: Analyze with LLM and generate ideas
    papers_summary = "\n".join([
        f"- {p.title} ({getattr(p, 'year', 'N/A')}) - {getattr(p, 'source', 'unknown')}: {(getattr(p, 'abstract', '') or '')[:150]}..."
        for p in unique_papers[:20]
    ])

    prompt = f"""You are a scientific research strategist. Analyze these recent papers on the topic "{topic}" and generate {num_ideas} novel, actionable research ideas.

Recent Papers ({len(unique_papers)} found):
{papers_summary}

For each idea, provide:
1. A clear, specific research idea title (one sentence)
2. A 2-3 sentence description of what would be investigated
3. Why it's important (1 sentence)
4. Expected approach/methodology (1 sentence)
5. Novelty level: high/medium/low

Format each idea exactly like this:
IDEA 1: [title]
DESCRIPTION: [description]
IMPORTANCE: [why important]
APPROACH: [methodology]
NOVELTY: [high/medium/low]
---

Generate ideas that are:
- Specific enough to be actionable
- Novel (not just repeating what's already been done)
- Feasible with current methods
- Addressing gaps, contradictions, or emerging trends in the literature"""

    response = await llm_router.complete(
        messages=[
            Message(role="system", content="You are a scientific research strategist."),
            Message(role="user", content=prompt),
        ],
        max_tokens=2000,
    )
    response_text = response.content
    ideas = []
    blocks = response_text.split("---")
    for block in blocks:
        block = block.strip()
        if not block or "IDEA" not in block:
            continue

        idea_data = {}
        for line in block.split("\n"):
            line = line.strip()
            if line.startswith("IDEA"):
                idea_data["title"] = line.split(":", 1)[1].strip() if ":" in line else ""
            elif line.startswith("DESCRIPTION"):
                idea_data["description"] = line.split(":", 1)[1].strip() if ":" in line else ""
            elif line.startswith("IMPORTANCE"):
                idea_data["importance"] = line.split(":", 1)[1].strip() if ":" in line else ""
            elif line.startswith("APPROACH"):
                idea_data["approach"] = line.split(":", 1)[1].strip() if ":" in line else ""
            elif line.startswith("NOVELTY"):
                idea_data["novelty"] = line.split(":", 1)[1].strip() if ":" in line else ""

        if idea_data.get("title"):
            ideas.append(idea_data)

    # Step 4: Save ideas to database
    idea_ledger = IdeaLedgerService(db)
    saved_ideas = []

    for idea_data in ideas[:num_ideas]:
        full_text = f"{idea_data['title']}\n\n{idea_data.get('description', '')}\n\nImportance: {idea_data.get('importance', '')}\n\nApproach: {idea_data.get('approach', '')}\n\nNovelty: {idea_data.get('novelty', 'medium')}"

        try:
            idea = await idea_ledger.create_idea(
                project_id=project_id,
                text=full_text,
                origin="literature_analysis",
                flexibility=0.7,
            )
            saved_ideas.append({
                "id": idea.id,
                "title": idea_data["title"],
                "description": idea_data.get("description", ""),
                "importance": idea_data.get("importance", ""),
                "approach": idea_data.get("approach", ""),
                "novelty": idea_data.get("novelty", "medium"),
            })
        except (ValueError, SQLAlchemyError) as e:
            logger.warning("idea_save_db_error", title=idea_data.get("title"), error=str(e))
        except Exception as e:
            logger.warning("idea_save_failed", title=idea_data.get("title"), error=str(e))

    await db.commit()

    return {
        "topic": topic,
        "papers_analyzed": len(unique_papers),
        "ideas_generated": len(saved_ideas),
        "ideas": saved_ideas,
    }


@router.get("/{idea_id}/versions", response_model=list[IdeaVersionResponse])
async def get_idea_versions(
    idea_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get idea version history."""
    service = IdeaService(db)
    versions = await service.get_idea_versions(idea_id)
    return versions


@router.get("/{idea_id}/decisions", response_model=list[IdeaDecisionResponse])
async def get_idea_decisions(
    idea_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get idea decision history."""
    service = IdeaService(db)
    decisions = await service.get_idea_decisions(idea_id)
    return decisions
