"""Cross-run wiki knowledge graph builder."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import KnowledgeNote


class WikiGraphService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_graph(self, project_id: str) -> dict:
        result = await self.db.execute(
            select(KnowledgeNote)
            .where(KnowledgeNote.project_id == project_id)
            .order_by(KnowledgeNote.created_at.asc()),
        )
        notes = list(result.scalars().all())

        nodes = [
            {
                "id": note.id,
                "title": note.title or "Untitled",
                "note_type": note.note_type,
                "run_id": note.run_id,
                "entity_id": note.entity_id,
            }
            for note in notes
        ]

        note_by_id = {n.id: n for n in notes}
        entity_index: dict[str, list[str]] = {}
        run_index: dict[str, list[str]] = {}
        edges: list[dict] = []
        seen_edges: set[tuple[str, str, str]] = set()

        def add_edge(source: str, target: str, edge_type: str, label: str = "") -> None:
            if source == target:
                return
            key = (source, target, edge_type)
            if key in seen_edges:
                return
            seen_edges.add(key)
            edges.append({
                "id": f"{source}-{target}-{edge_type}",
                "source": source,
                "target": target,
                "type": edge_type,
                "label": label,
            })

        for note in notes:
            if note.entity_id:
                entity_index.setdefault(note.entity_id, []).append(note.id)
            if note.run_id:
                run_index.setdefault(note.run_id, []).append(note.id)

            for linked_id in note.linked_notes or []:
                if linked_id in note_by_id:
                    add_edge(note.id, linked_id, "link", "linked")

        for entity_id, note_ids in entity_index.items():
            for i, src in enumerate(note_ids):
                for tgt in note_ids[i + 1 :]:
                    add_edge(src, tgt, "entity", entity_id[:12])

        for run_id, note_ids in run_index.items():
            for i, src in enumerate(note_ids):
                for tgt in note_ids[i + 1 :]:
                    add_edge(src, tgt, "run", run_id[:8])

        return {
            "project_id": project_id,
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "note_count": len(nodes),
                "edge_count": len(edges),
                "run_count": len(run_index),
            },
        }
