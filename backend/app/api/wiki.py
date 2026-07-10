"""Knowledge wiki API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.dependencies.auth import get_current_user, require_project_role
from app.models.collaboration import User
from app.schemas.report import KnowledgeNoteResponse
from app.services.report_service import KnowledgeService

router = APIRouter()


@router.get("/graph")
async def wiki_knowledge_graph(
    project_id: Annotated[str, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Cross-run knowledge graph linking wiki notes by entity, run, and links."""
    from app.services.wiki_graph_service import WikiGraphService

    service = WikiGraphService(db)
    return await service.build_graph(project_id)


@router.get("/search/semantic")
async def semantic_wiki_search(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Annotated[str, Query()],
    q: Annotated[str, Query(min_length=3)],
    run_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
):
    """Semantic search over wiki notes using embeddings."""
    from app.api.research import get_llm_router
    from app.services.embedding_service import EmbeddingService
    from app.services.wiki_embedding_service import WikiEmbeddingService

    embedding = EmbeddingService(db, get_llm_router())
    wiki_embed = WikiEmbeddingService(db, embedding)
    try:
        results = await wiki_embed.search_semantic(project_id, q, run_id=run_id, limit=limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"query": q, "results": results}


@router.post("/embed")
async def embed_wiki_notes(
    project_id: Annotated[str, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    await require_project_role(db, project_id, user.id, "editor")
    """Backfill embeddings for project wiki notes."""
    from app.api.research import get_llm_router
    from app.services.embedding_service import EmbeddingService
    from app.services.wiki_embedding_service import WikiEmbeddingService

    embedding = EmbeddingService(db, get_llm_router())
    wiki_embed = WikiEmbeddingService(db, embedding)
    try:
        count = await wiki_embed.embed_project_notes(project_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    await db.commit()
    return {"embedded": count}


@router.get("/search", response_model=list[KnowledgeNoteResponse])
async def search_wiki_notes(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Annotated[str, Query()],
    q: Annotated[str, Query(min_length=2)],
    run_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    """Search knowledge notes by title or content."""
    service = KnowledgeService(db)
    return await service.search_notes(project_id, q, run_id=run_id, limit=limit)


@router.get("", response_model=list[KnowledgeNoteResponse])
async def list_wiki_notes(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Annotated[str, Query()],
    note_type: Annotated[str | None, Query()] = None,
    run_id: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List knowledge notes for a project."""
    service = KnowledgeService(db)
    notes = await service.list_notes(project_id, note_type, run_id, page, per_page)
    return notes


@router.get("/{note_id}", response_model=KnowledgeNoteResponse)
async def get_wiki_note(
    note_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a knowledge note."""
    service = KnowledgeService(db)
    note = await service.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.post("", response_model=KnowledgeNoteResponse, status_code=201)
async def create_wiki_note(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    project_id: Annotated[str, Query()],
    title: Annotated[str, Query()],
    content: Annotated[str, Query()],
    note_type: Annotated[str | None, Query()] = None,
    entity_id: Annotated[str | None, Query()] = None,
    run_id: Annotated[str | None, Query()] = None,
):
    """Create a new knowledge note."""
    await require_project_role(db, project_id, user.id, "editor")
    service = KnowledgeService(db)
    note = await service.create_note(
        project_id=project_id,
        note_type=note_type or "general",
        title=title,
        content=content,
        entity_id=entity_id,
        run_id=run_id,
    )
    return note


@router.put("/{note_id}", response_model=KnowledgeNoteResponse)
async def update_wiki_note(
    note_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    title: Annotated[str | None, Query()] = None,
    content: Annotated[str | None, Query()] = None,
):
    """Update a knowledge note."""
    from sqlalchemy import select as sql_select

    from app.models.report import KnowledgeNote as NoteModel

    result = await db.execute(sql_select(NoteModel).where(NoteModel.id == note_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Note not found")
    await require_project_role(db, existing.project_id, user.id, "editor")

    service = KnowledgeService(db)
    note = await service.update_note(note_id, title=title, content=content)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/{note_id}", status_code=204)
async def delete_wiki_note(
    note_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Delete a knowledge note."""
    from sqlalchemy import select as sql_select

    from app.models.report import KnowledgeNote as NoteModel
    from app.services.audit_service import AuditService

    result = await db.execute(sql_select(NoteModel).where(NoteModel.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    await require_project_role(db, note.project_id, user.id, "editor")

    service = KnowledgeService(db)
    await service.delete_note(note_id)

    audit = AuditService(db)
    await audit.log_event(
        event_type="wiki_note_deleted",
        project_id=note.project_id,
        actor="user",
        action=f"Deleted wiki note {note_id}",
    )
    await db.commit()
