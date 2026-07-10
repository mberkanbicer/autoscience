"""Project API endpoints."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.dependencies.auth import get_current_user, require_project_role
from app.models.collaboration import ProjectMember, User
from app.models.project import Project
from app.schemas.project import (
    GraphEdge,
    GraphNode,
    ProjectCreate,
    ProjectGraphResponse,
    ProjectResponse,
    ProjectStats,
    ProjectUpdate,
)

router = APIRouter()


@router.get("/domain-packs/list")
async def list_domain_packs():
    """List available domain specialization packs."""
    from app.engine.domain_packs import list_domain_packs as _list_packs

    return _list_packs()


@router.post("/{project_id}/apply-domain-pack", response_model=ProjectResponse)
async def apply_domain_pack(
    project_id: str,
    pack_id: Annotated[str, Query(pattern="^(physics|biology|chemistry)$")],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Apply a domain pack to project scope and metadata."""
    from app.engine.domain_packs import apply_domain_pack as _apply_pack

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await require_project_role(db, project_id, user.id, "owner")

    try:
        updates = _apply_pack(pack_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    project.domain = updates["domain"]
    project.description = updates["description"]
    project.subject_scope = updates["subject_scope"]
    project.out_of_scope = updates["out_of_scope"]
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[Project]:
    """List all projects."""
    offset = (page - 1) * per_page
    result = await db.execute(select(Project).offset(offset).limit(per_page))
    return result.scalars().all()


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_in: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Project:
    """Create a new project, optionally scoped to an organization."""
    # Validate organization if provided
    if project_in.organization_id:
        from app.models.organization import Organization, OrganizationMember

        org_result = await db.execute(
            select(Organization).where(Organization.id == project_in.organization_id),
        )
        org = org_result.scalar_one_or_none()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # Verify user is a member of the org
        member_result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == project_in.organization_id,
                OrganizationMember.user_id == user.id,
            ),
        )
        if not member_result.scalar_one_or_none():
            raise HTTPException(
                status_code=403,
                detail="User is not a member of this organization",
            )

        # Check org project limit
        from sqlalchemy import func

        project_count = await db.execute(
            select(func.count(Project.id)).where(
                Project.organization_id == project_in.organization_id,
            ),
        )
        if org.max_projects and project_count.scalar() >= org.max_projects:
            raise HTTPException(
                status_code=403,
                detail="Organization has reached its project limit",
            )

    project = Project(
        id=str(uuid4()),
        organization_id=project_in.organization_id,
        name=project_in.name,
        domain=project_in.domain,
        description=project_in.description,
        subject_scope=project_in.subject_scope,
        out_of_scope=project_in.out_of_scope,
        default_flexibility=project_in.default_flexibility,
        idle_research_enabled=project_in.idle_research_enabled,
        idle_trigger_minutes=project_in.idle_trigger_minutes,
        max_idle_cycles_per_day=project_in.max_idle_cycles_per_day,
        max_sources_per_cycle=project_in.max_sources_per_cycle,
        approval_required_for_external_actions=project_in.approval_required_for_external_actions,
    )
    db.add(project)
    await db.flush()
    db.add(
        ProjectMember(
            id=str(uuid4()),
            project_id=project.id,
            user_id=user.id,
            role="owner",
        ),
    )
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Project:
    """Get a project by ID."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Project:
    """Update a project."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await require_project_role(db, project_id, user.id, "owner")

    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a project and all related entities (via database cascades)."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await require_project_role(db, project_id, user.id, "owner")

    await db.delete(project)
    await db.commit()


@router.get("/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectStats:
    """Get project statistics."""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Count ideas
    from app.models.idea import Idea

    idea_counts = await db.execute(
        select(
            func.count(Idea.id).label("total"),
            func.count(Idea.id).filter(Idea.status == "active").label("active"),
            func.count(Idea.id).filter(Idea.status == "rejected").label("rejected"),
        ).where(Idea.project_id == project_id),
    )
    idea_row = idea_counts.one()

    # Count runs
    from app.models.research_run import ResearchRun

    run_counts = await db.execute(
        select(
            func.count(ResearchRun.id).label("total"),
            func.count(ResearchRun.id).filter(ResearchRun.state == "running").label("active"),
        ).where(ResearchRun.project_id == project_id),
    )
    run_row = run_counts.one()

    # Count papers
    from app.models.paper import Paper

    paper_count = await db.execute(
        select(func.count(Paper.id)).where(Paper.project_id == project_id),
    )

    # Count skills
    from app.models.skill import Skill

    skill_count = await db.execute(
        select(func.count(Skill.id)).where(Skill.project_id == project_id),
    )

    # Count conflicts
    from app.models.paper import ClusterConflict

    conflict_count = await db.execute(
        select(func.count(ClusterConflict.id)).where(ClusterConflict.project_id == project_id),
    )

    # Count questions
    from app.models.research_question import ResearchQuestion

    question_count = await db.execute(
        select(func.count(ResearchQuestion.id)).where(ResearchQuestion.project_id == project_id),
    )

    # Count hypotheses
    from app.models.research_question import Hypothesis

    hypothesis_count = await db.execute(
        select(func.count(Hypothesis.id)).where(Hypothesis.project_id == project_id),
    )

    # Count scores (via ideas table)
    from app.models.idea import IdeaScore

    await db.execute(
        select(func.count(IdeaScore.id)).where(IdeaScore.idea_id.in_(
            select(Idea.id).where(Idea.project_id == project_id),
        )),
    )

    # Count reports
    from app.models.report import ResearchReport

    report_count = await db.execute(
        select(func.count(ResearchReport.id)).where(ResearchReport.project_id == project_id),
    )

    # Count wiki notes
    from app.models.report import KnowledgeNote

    wiki_count = await db.execute(
        select(func.count(KnowledgeNote.id)).where(KnowledgeNote.project_id == project_id),
    )

    # Count clusters
    from app.models.paper import PaperCluster

    cluster_count = await db.execute(
        select(func.count(PaperCluster.id)).where(PaperCluster.project_id == project_id),
    )

    # Latest cognitive metrics
    latest_run_result = await db.execute(
        select(ResearchRun.cognitive_entropy, ResearchRun.cognitive_mode)
        .where(ResearchRun.project_id == project_id)
        .where(ResearchRun.state == "completed")
        .order_by(ResearchRun.completed_at.desc())
        .limit(1),
    )
    latest_run = latest_run_result.first()

    entropy = latest_run[0] if latest_run else None
    mode = latest_run[1] if latest_run else None

    # Active run phase
    active_phase = None
    if run_row.active > 0:
        active_run_result = await db.execute(
            select(ResearchRun.current_phase)
            .where(ResearchRun.project_id == project_id)
            .where(ResearchRun.state == "running")
            .limit(1),
        )
        active_phase = active_run_result.scalar()

    # Fallback: if we have runs but no metrics (legacy data), compute on the fly
    if entropy is None and run_row.total > 0:
        # Get distribution of papers across clusters for this project
        cluster_papers_result = await db.execute(
            select(PaperCluster.paper_ids)
            .where(PaperCluster.project_id == project_id),
        )
        all_clusters = cluster_papers_result.scalars().all()

        # Correctly extract lengths from non-null paper_ids lists
        paper_counts = [len(pids) for pids in all_clusters if pids is not None and len(pids) > 0]
        total_p = sum(paper_counts)

        if total_p > 0 and len(paper_counts) > 1:
            import math
            p_i = [c / total_p for c in paper_counts if c > 0]
            shannon = -sum(p * math.log2(p) for p in p_i)
            max_h = math.log2(len(paper_counts))
            entropy = round(shannon / max_h, 2) if max_h > 0 else 0.5

            if entropy > 0.7: mode = "exploration"
            elif entropy < 0.3: mode = "exploitation"
            else: mode = "balanced"
        elif run_row.total > 0:
            # We have research but no clustering data yet
            entropy = 0.50
            mode = "balanced"
        elif total_p > 0:
            # We have papers but only one cluster or concentrated assignments
            entropy = 0.20
            mode = "exploitation"

    # Compute Focus metric from entropy + cluster diversity
    # Focus = 1.0 - normalized_entropy (distribution evenness)
    # blended with cluster_concentration (fewer clusters = more focus)
    # 1.0 = max depth (all papers in few clusters), 0.0 = max breadth
    focus_score = None
    focus_label = None
    if entropy is not None:
        paper_count = paper_count.scalar() or 0
        cluster_count = cluster_count.scalar() or 0

        # Evenness component: how evenly papers are spread across clusters
        evenness_focus = 1.0 - entropy

        # Concentration component: fewer clusters per paper = more focused
        if paper_count > 0 and cluster_count > 0:
            diversity_ratio = cluster_count / paper_count
            cluster_concentration = 1.0 / (1.0 + diversity_ratio)
        else:
            cluster_concentration = 0.5

        # Blend: 70% evenness, 30% absolute cluster count
        focus_score = round(0.7 * evenness_focus + 0.3 * cluster_concentration, 2)

        if focus_score > 0.7:
            focus_label = "deep_dive"
        elif focus_score < 0.3:
            focus_label = "broad_scan"
        else:
            focus_label = "balanced"

    return ProjectStats(
        total_ideas=idea_row.total,
        active_ideas=idea_row.active,
        rejected_ideas=idea_row.rejected,
        total_runs=run_row.total,
        active_runs=run_row.active,
        total_papers=paper_count.scalar() or 0,
        total_skills=skill_count.scalar() or 0,
        total_conflicts=conflict_count.scalar() or 0,
        total_questions=question_count.scalar() or 0,
        total_hypotheses=hypothesis_count.scalar() or 0,
        total_reports=report_count.scalar() or 0,
        total_wiki_notes=wiki_count.scalar() or 0,
        total_clusters=cluster_count.scalar() or 0,
        latest_cognitive_entropy=entropy,
        latest_cognitive_mode=mode,
        latest_focus_score=focus_score,
        latest_focus_label=focus_label,
        active_run_phase=active_phase,
    )


@router.get("/{project_id}/graph", response_model=ProjectGraphResponse)
async def get_project_graph(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectGraphResponse:
    """Generate interactive knowledge graph for scientific papers."""
    from app.models.paper import ClusterConflict, Paper, PaperCluster

    # 1. Fetch Papers
    papers_result = await db.execute(select(Paper).where(Paper.project_id == project_id))
    papers = papers_result.scalars().all()

    # 2. Fetch Clusters
    clusters_result = await db.execute(select(PaperCluster).where(PaperCluster.project_id == project_id))
    clusters = clusters_result.scalars().all()

    # 3. Fetch Conflicts
    conflicts_result = await db.execute(select(ClusterConflict).where(ClusterConflict.project_id == project_id))
    conflicts = conflicts_result.scalars().all()

    # Map paper DOI/ID to our DB ID for easy linking
    paper_lookup = {}
    nodes = []

    # Track which paper belongs to which cluster
    paper_to_cluster = {}
    for cluster in clusters:
        for pid in (cluster.paper_ids or []):
            paper_to_cluster[pid] = cluster.id

    for paper in papers:
        # Priority for linking: DOI > source_id > title_hash
        if paper.doi: paper_lookup[paper.doi.strip().lower()] = paper.id
        if paper.source_id: paper_lookup[paper.source_id.strip().lower()] = paper.id

        nodes.append(GraphNode(
            id=paper.id,
            title=paper.title,
            year=paper.year,
            cluster_id=paper_to_cluster.get(paper.id),
            paper_type=paper.paper_type,
            citation_count=paper.citation_count or 0,
        ))

    edges = []
    edge_counter = 0

    # 4. Generate Citation Edges
    for paper in papers:
        refs = paper.references or []
        for ref in refs:
            normalized_ref = ref.strip().lower()
            if normalized_ref in paper_lookup:
                target_id = paper_lookup[normalized_ref]
                if target_id != paper.id: # Avoid self-loops
                    edges.append(GraphEdge(
                        id=f"cit-{edge_counter}",
                        source=paper.id,
                        target=target_id,
                        type="citation",
                    ))
                    edge_counter += 1

    # 5. Generate Conflict Edges
    for conflict in conflicts:
        # A conflict typically involves two or more papers
        # We'll link supporting vs opposing if they are in our DB
        supports = [s for s in conflict.supporting_papers if s in paper_lookup or any(p.id == s for p in papers)]
        opposes = [o for o in conflict.opposing_papers if o in paper_lookup or any(p.id == o for p in papers)]

        for s_ref in supports:
            s_id = paper_lookup.get(s_ref.strip().lower()) or next((p.id for p in papers if p.id == s_ref), None)
            for o_ref in opposes:
                o_id = paper_lookup.get(o_ref.strip().lower()) or next((p.id for p in papers if p.id == o_ref), None)
                if s_id and o_id:
                    edges.append(GraphEdge(
                        id=f"con-{edge_counter}",
                        source=s_id,
                        target=o_id,
                        type="conflict",
                        label=conflict.conflict_type,
                        severity=conflict.severity,
                    ))
                    edge_counter += 1

    # 6. Generate Semantic (Cluster) Edges (link papers within the same cluster to form a web)
    for cluster in clusters:
        cluster_pids = [pid for pid in (cluster.paper_ids or []) if any(p.id == pid for p in papers)]
        if len(cluster_pids) > 1:
            # Connect all to representative if exists, else first
            root_id = cluster.representative_paper_id or cluster_pids[0]
            for pid in cluster_pids:
                if pid != root_id:
                    edges.append(GraphEdge(
                        id=f"sem-{edge_counter}",
                        source=root_id,
                        target=pid,
                        type="semantic",
                        label="Same Theme",
                    ))
                    edge_counter += 1

    return ProjectGraphResponse(nodes=nodes, edges=edges)


@router.get("/{project_id}/idle-cycles")
async def list_idle_cycles(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List recent idle cognition cycles for a project."""
    from app.services.idle_cycle_service import IdleCycleService

    result = await db.execute(select(Project).where(Project.id == project_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    service = IdleCycleService(db)
    cycles = await service.get_project_cycles(project_id, limit=limit)
    stats = await service.get_cycle_statistics(project_id)
    return {"cycles": cycles, "statistics": stats}


@router.get("/{project_id}/activity")
async def project_activity_feed(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    """Unified activity feed (audit, comments, reviews)."""
    from app.services.activity_feed_service import ActivityFeedService

    result = await db.execute(select(Project).where(Project.id == project_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    service = ActivityFeedService(db)
    return await service.get_feed(project_id, limit=limit)


@router.get("/{project_id}/audit/export")
async def export_audit_trail(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    format: Annotated[str, Query(pattern="^(json|csv)$")] = "json",
):
    """Export project audit trail."""
    import csv
    import io
    import json

    from fastapi.responses import Response

    from app.models.audit import AuditLog

    result = await db.execute(select(Project).where(Project.id == project_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    logs_result = await db.execute(
        select(AuditLog)
        .where(AuditLog.project_id == project_id)
        .order_by(AuditLog.created_at.desc()),
    )
    rows = [
        {
            "id": log.id,
            "event_type": log.event_type,
            "actor": log.actor,
            "action": log.action,
            "run_id": log.run_id,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs_result.scalars().all()
    ]

    if format == "csv":
        buffer = io.StringIO()
        if rows:
            writer = csv.DictWriter(buffer, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return Response(
            content=buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="audit-{project_id}.csv"'},
        )

    return Response(
        content=json.dumps(rows, indent=2, default=str),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="audit-{project_id}.json"'},
    )

