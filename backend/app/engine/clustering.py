"""Paper clustering engine for grouping papers into themes."""

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import structlog

from ..llm.base import Message
from ..llm.router import LLMRouter

logger = structlog.get_logger()


@dataclass
class PaperCluster:
    """A cluster of related papers."""

    id: str
    name: str
    description: str
    cluster_type: str  # topic, method, dataset, claim
    paper_ids: list[str] = field(default_factory=list)
    representative_paper_id: str | None = None
    labels: list[str] = field(default_factory=list)
    size: int = 0
    coherence_score: float = 0.0


@dataclass
class ClusteringResult:
    """Result from paper clustering."""

    clusters: list[PaperCluster] = field(default_factory=list)
    paper_to_cluster: dict[str, str] = field(default_factory=dict)
    clustering_notes: str = ""
    total_clusters: int = 0
    avg_cluster_size: float = 0.0


class ClusteringEngine:
    """Engine for clustering papers into themes."""

    def __init__(self, llm_router: LLMRouter):
        self.llm = llm_router

    async def cluster_papers(
        self,
        papers: list[dict[str, Any]],
        cluster_type: str = "topic",
        max_clusters: int = 10,
    ) -> ClusteringResult:
        """Cluster papers into themes."""
        if not papers:
            return ClusteringResult()

        # Prepare paper summaries
        papers_summary = self._prepare_papers_summary(papers)

        # Generate clusters using LLM
        clusters_data = await self._generate_clusters(
            papers_summary=papers_summary,
            cluster_type=cluster_type,
            max_clusters=max_clusters,
        )

        # Create cluster objects
        clusters = []
        paper_to_cluster = {}

        for cluster_data in clusters_data.get("clusters", []):
            cluster = PaperCluster(
                id=str(uuid4()),
                name=cluster_data.get("name", "Unnamed Cluster"),
                description=cluster_data.get("description", ""),
                cluster_type=cluster_type,
                paper_ids=cluster_data.get("paper_ids", []),
                labels=cluster_data.get("labels", []),
                size=len(cluster_data.get("paper_ids", [])),
            )
            clusters.append(cluster)

            # Map papers to cluster
            for paper_id in cluster.paper_ids:
                paper_to_cluster[paper_id] = cluster.id

        # Select representative papers
        await self._select_representatives(clusters, papers)

        # Calculate coherence scores
        await self._calculate_coherence(clusters, papers)

        # Generate clustering notes
        notes = await self._generate_clustering_notes(clusters, papers)

        # Calculate statistics
        total_clusters = len(clusters)
        avg_size = sum(c.size for c in clusters) / total_clusters if total_clusters > 0 else 0

        return ClusteringResult(
            clusters=clusters,
            paper_to_cluster=paper_to_cluster,
            clustering_notes=notes,
            total_clusters=total_clusters,
            avg_cluster_size=avg_size,
        )

    def _prepare_papers_summary(self, papers: list[dict[str, Any]]) -> str:
        """Prepare a summary of papers for clustering."""
        summaries = []
        for i, paper in enumerate(papers[:50]):  # Limit to 50 papers
            summary = f"Paper {i+1} (ID: {paper.get('id', 'unknown')}):\n"
            summary += f"Title: {paper.get('title', 'Unknown')}\n"
            if paper.get("abstract"):
                summary += f"Abstract: {paper['abstract'][:200]}...\n"
            if paper.get("method"):
                summary += f"Method: {paper['method']}\n"
            if paper.get("findings"):
                summary += f"Findings: {', '.join(paper['findings'][:3])}\n"
            summaries.append(summary)

        return "\n".join(summaries)

    async def _generate_clusters(
        self,
        papers_summary: str,
        cluster_type: str,
        max_clusters: int,
    ) -> dict[str, Any]:
        """Generate clusters using LLM."""
        cluster_type_instructions = {
            "topic": "Group papers by their main research topic or theme",
            "method": "Group papers by the methods or techniques they use",
            "dataset": "Group papers by the datasets or data sources they use",
            "claim": "Group papers by their main claims or findings",
        }

        instruction = cluster_type_instructions.get(
            cluster_type,
            "Group papers by similarity",
        )

        system = f"""You are a scientific paper clustering expert.

Your task is to {instruction}.

Output a JSON object with:
- clusters: Array of cluster objects, each with:
  - name: Descriptive cluster name (string)
  - description: Brief description of the cluster theme (string)
  - paper_ids: List of paper IDs belonging to this cluster (array of strings)
  - labels: Key terms or labels for this cluster (array of strings)

Guidelines:
- Create between 3 and {max_clusters} clusters
- Each paper should belong to exactly one cluster
- Cluster names should be concise and descriptive
- Prioritize meaningful groupings over equal sizes"""

        user = f"""Papers to cluster:
{papers_summary}

Create {cluster_type} clusters for these papers as JSON."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})
        return result.data

    async def _select_representatives(
        self,
        clusters: list[PaperCluster],
        papers: list[dict[str, Any]],
    ) -> None:
        """Select representative paper for each cluster."""
        # Create paper lookup
        paper_lookup = {p.get("id"): p for p in papers}

        for cluster in clusters:
            if not cluster.paper_ids:
                continue

            # Find the paper with most citations in the cluster
            best_paper = None
            best_citations = -1

            for paper_id in cluster.paper_ids:
                paper = paper_lookup.get(paper_id)
                if paper:
                    citations = paper.get("citation_count", 0) or 0
                    if citations > best_citations:
                        best_citations = citations
                        best_paper = paper_id

            cluster.representative_paper_id = best_paper or cluster.paper_ids[0]

    async def _calculate_coherence(
        self,
        clusters: list[PaperCluster],
        papers: list[dict[str, Any]],
    ) -> None:
        """Calculate coherence score for each cluster."""
        paper_lookup = {p.get("id"): p for p in papers}

        for cluster in clusters:
            if len(cluster.paper_ids) < 2:
                cluster.coherence_score = 1.0
                continue

            # Simple coherence based on title similarity
            cluster_papers = [
                paper_lookup.get(pid, {})
                for pid in cluster.paper_ids
                if pid in paper_lookup
            ]

            titles = [p.get("title", "") for p in cluster_papers]
            # Use LLM to assess coherence
            coherence = await self._assess_cluster_coherence(titles)
            cluster.coherence_score = coherence

    async def _assess_cluster_coherence(self, titles: list[str]) -> float:
        """Assess coherence of a cluster based on titles."""
        if len(titles) < 2:
            return 1.0

        titles_text = "\n".join([f"- {t}" for t in titles[:10]])

        system = """You are a research cluster quality assessor.

Assess how coherent this cluster of papers is based on their titles.

Output a JSON object with:
- coherence: Score from 0 to 1 (1 = very coherent, 0 = not coherent)
- reason: Brief explanation"""

        user = f"""Paper titles in cluster:
{titles_text}

Assess the coherence of this cluster."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        try:
            result = await self.llm.complete_structured(messages, schema={})
            return result.data.get("coherence", 0.5)
        except Exception:
            return 0.5

    async def _generate_clustering_notes(
        self,
        clusters: list[PaperCluster],
        papers: list[dict[str, Any]],
    ) -> str:
        """Generate notes about the clustering results."""
        cluster_summary = "\n".join(
            [
                f"- {c.name} ({c.size} papers, coherence: {c.coherence_score:.2f})"
                for c in clusters
            ]
        )

        system = """You are a research literature analyst.

Given a set of paper clusters, provide brief notes on:
1. Overview of the clustering results
2. Key themes identified
3. Notable patterns
4. Potential gaps or overlaps

Keep it concise (2-3 paragraphs)."""

        user = f"""Clustering results ({len(clusters)} clusters, {len(papers)} papers):

{cluster_summary}

Provide notes on the clustering results."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete(messages, temperature=0.3, max_tokens=500)
        return result.content

    async def merge_clusters(
        self,
        clusters: list[PaperCluster],
        similarity_threshold: float = 0.8,
    ) -> list[PaperCluster]:
        """Merge similar clusters."""
        if len(clusters) <= 1:
            return clusters

        # Find clusters to merge
        merge_pairs = []
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                similarity = await self._calculate_cluster_similarity(
                    clusters[i], clusters[j]
                )
                if similarity >= similarity_threshold:
                    merge_pairs.append((i, j))

        # Merge clusters (in reverse order to maintain indices)
        merged_indices = set()
        for i, j in reversed(merge_pairs):
            if i not in merged_indices and j not in merged_indices:
                # Merge j into i
                clusters[i].paper_ids.extend(clusters[j].paper_ids)
                clusters[i].size = len(clusters[i].paper_ids)
                clusters[i].name = f"{clusters[i].name} / {clusters[j].name}"
                merged_indices.add(j)

        # Remove merged clusters
        return [c for i, c in enumerate(clusters) if i not in merged_indices]

    async def _calculate_cluster_similarity(
        self,
        cluster1: PaperCluster,
        cluster2: PaperCluster,
    ) -> float:
        """Calculate similarity between two clusters."""
        # Simple similarity based on name overlap
        words1 = set(cluster1.name.lower().split())
        words2 = set(cluster2.name.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0
