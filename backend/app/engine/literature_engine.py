"""Literature retrieval and ranking engine."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog

from ..connectors.base import RawPaper, SearchQuery, SearchResult
from ..connectors.manager import ConnectorManager
from ..llm.base import Message
from ..llm.router import LLMRouter

logger = structlog.get_logger()


@dataclass
class RankedPaper:
    """A paper with relevance ranking."""

    paper: RawPaper
    relevance_score: float = 0.0
    citation_score: float = 0.0
    recency_score: float = 0.0
    venue_score: float = 0.0
    review_score: float = 0.0
    overall_score: float = 0.0
    selection_reason: str = ""


@dataclass
class LiteratureResult:
    """Result from literature retrieval."""

    idea: str
    papers: list[RankedPaper] = field(default_factory=list)
    high_impact_papers: list[RankedPaper] = field(default_factory=list)
    frontier_papers: list[RankedPaper] = field(default_factory=list)
    review_papers: list[RankedPaper] = field(default_factory=list)
    search_queries_used: list[str] = field(default_factory=list)
    total_found: int = 0
    retrieval_notes: str = ""


class LiteratureEngine:
    """Engine for retrieving and ranking academic literature."""

    def __init__(self, llm_router: LLMRouter, connector_manager: ConnectorManager):
        self.llm = llm_router
        self.connectors = connector_manager

    async def retrieve_literature(
        self,
        idea: str,
        keywords: list[str] | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        limit: int = 50,
        sources: list[str] | None = None,
    ) -> LiteratureResult:
        """Retrieve relevant literature for an idea."""
        # Build search query
        search_text = " ".join(keywords[:5]) if keywords else idea

        query = SearchQuery(
            text=search_text,
            year_from=year_from or (datetime.now().year - 5),
            year_to=year_to or datetime.now().year,
            limit=limit,
            sort_by="relevance",
        )

        # Search across sources
        search_results = await self.connectors.search_all(query, sources)

        # Merge and rank papers
        all_papers = []
        for source, result in search_results.items():
            all_papers.extend(result.papers)

        # Rank papers
        ranked_papers = await self._rank_papers(idea, all_papers)

        # Categorize papers
        high_impact = [p for p in ranked_papers if p.citation_score > 0.7][:20]
        frontier = [p for p in ranked_papers if p.recency_score > 0.8][:20]
        reviews = [p for p in ranked_papers if p.review_score > 0.5][:10]

        # Generate retrieval notes (skip if no LLM)
        try:
            notes = await self._generate_retrieval_notes(idea, ranked_papers)
        except Exception:
            notes = f"Found {len(ranked_papers)} papers for: {idea[:100]}"

        return LiteratureResult(
            idea=idea,
            papers=ranked_papers[:limit],
            high_impact_papers=high_impact,
            frontier_papers=frontier,
            review_papers=reviews,
            search_queries_used=[query.text],
            total_found=len(all_papers),
            retrieval_notes=notes,
        )

    async def search_by_query_type(
        self,
        idea: str,
        query_type: str,
        keywords: list[str] | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        limit: int = 20,
    ) -> list[RankedPaper]:
        """Search for papers by query type."""
        search_text = " ".join(keywords[:5]) if keywords else idea

        # Add query type specific terms
        if query_type == "review":
            search_text += " AND (review OR survey OR overview)"
        elif query_type == "frontier":
            year_from = datetime.now().year - 1
            year_to = datetime.now().year
        elif query_type == "contradiction":
            search_text += " AND (contradict OR challenge OR limitation)"

        query = SearchQuery(
            text=search_text,
            year_from=year_from,
            year_to=year_to,
            limit=limit,
            sort_by="citations" if query_type == "high_impact" else "relevance",
        )

        results = await self.connectors.search_all(query)
        all_papers = []
        for result in results.values():
            all_papers.extend(result.papers)

        return await self._rank_papers(idea, all_papers)

    async def _rank_papers(self, idea: str, papers: list[RawPaper]) -> list[RankedPaper]:
        """Rank papers based on relevance to the idea."""
        if not papers:
            return []

        # Use LLM to assess relevance for top candidates
        # First, do quick scoring based on metadata
        ranked = []
        current_year = datetime.now().year

        for paper in papers:
            ranked_paper = RankedPaper(paper=paper)

            # Citation score (0-1)
            if paper.citation_count:
                if paper.citation_count > 1000:
                    ranked_paper.citation_score = 1.0
                elif paper.citation_count > 100:
                    ranked_paper.citation_score = 0.8
                elif paper.citation_count > 10:
                    ranked_paper.citation_score = 0.6
                else:
                    ranked_paper.citation_score = 0.3
            else:
                ranked_paper.citation_score = 0.2

            # Recency score (0-1)
            if paper.year:
                years_old = current_year - paper.year
                if years_old <= 1:
                    ranked_paper.recency_score = 1.0
                elif years_old <= 3:
                    ranked_paper.recency_score = 0.8
                elif years_old <= 5:
                    ranked_paper.recency_score = 0.6
                else:
                    ranked_paper.recency_score = 0.3
            else:
                ranked_paper.recency_score = 0.5

            # Venue score (0-1)
            if paper.venue:
                high_impact_venues = [
                    "nature", "science", "cell", "lancet",
                    "ieee", "acm", "neurips", "icml", "iclr", "aaai",
                    "acl", "emnlp", "naacl", "cvpr", "iccv",
                ]
                venue_lower = paper.venue.lower()
                if any(v in venue_lower for v in high_impact_venues):
                    ranked_paper.venue_score = 1.0
                else:
                    ranked_paper.venue_score = 0.5
            else:
                ranked_paper.venue_score = 0.3

            # Review score (0-1)
            if paper.paper_type == "review":
                ranked_paper.review_score = 1.0
            elif paper.title:
                title_lower = paper.title.lower()
                if any(w in title_lower for w in ["review", "survey", "overview"]):
                    ranked_paper.review_score = 0.9
                else:
                    ranked_paper.review_score = 0.1

            # Overall score (weighted combination)
            ranked_paper.overall_score = (
                0.3 * ranked_paper.citation_score
                + 0.25 * ranked_paper.recency_score
                + 0.2 * ranked_paper.venue_score
                + 0.15 * ranked_paper.relevance_score
                + 0.1 * ranked_paper.review_score
            )

            ranked.append(ranked_paper)

        # Sort by overall score
        ranked.sort(key=lambda p: p.overall_score, reverse=True)

        # Use LLM to refine top 20 rankings (only if LLM provider available)
        if len(ranked) > 20 and self.llm.has_provider():
            top_20 = ranked[:20]
            refined = await self._llm_rank_top_papers(idea, top_20)
            ranked = refined + ranked[20:]
        elif len(ranked) > 20:
            logger.info("skipping_llm_ranking_no_provider")

        return ranked

    async def _llm_rank_top_papers(self, idea: str, papers: list[RankedPaper]) -> list[RankedPaper]:
        """Use LLM to refine ranking of top papers."""
        papers_summary = "\n".join(
            [
                f"{i+1}. [{p.paper.citation_count or 0} citations] {p.paper.title} ({p.paper.year})"
                for i, p in enumerate(papers)
            ]
        )

        system = """You are a scientific literature ranking expert.

Given a research idea and a list of papers, rank them by relevance.

Output a JSON object with:
- rankings: Array of objects with:
  - index: Paper number (0-based)
  - relevance: Relevance score 0-10
  - reason: Brief reason for the ranking

Consider:
- How directly the paper addresses the idea
- Whether it provides foundational knowledge
- Whether it presents conflicting evidence
- Whether it offers methods applicable to the idea"""

        user = f"""Research idea: {idea}

Papers:
{papers_summary}

Rank these papers by relevance as JSON."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        try:
            result = await self.llm.complete_structured(messages, schema={})
            rankings = result.data.get("rankings", [])

            # Apply rankings
            for ranking in rankings:
                idx = ranking.get("index", 0)
                if 0 <= idx < len(papers):
                    papers[idx].relevance_score = ranking.get("relevance", 5) / 10
                    papers[idx].selection_reason = ranking.get("reason", "")

            # Re-sort by updated scores
            papers.sort(key=lambda p: p.overall_score, reverse=True)

        except Exception as e:
            logger.error("llm_ranking_failed", error=str(e))

        return papers

    async def _generate_retrieval_notes(
        self, idea: str, papers: list[RankedPaper]
    ) -> str:
        """Generate notes about the literature retrieval."""
        if not papers:
            return "No relevant papers found."

        system = """You are a research literature analyst.

Given a research idea and retrieved papers, provide brief notes on:
1. What was found
2. Key themes in the literature
3. Potential gaps
4. Notable papers
5. Recommendations for next steps

Keep it concise (2-3 paragraphs)."""

        papers_summary = "\n".join(
            [f"- {p.paper.title} ({p.paper.year})" for p in papers[:10]]
        )

        user = f"""Idea: {idea}

Top retrieved papers:
{papers_summary}

Provide brief literature retrieval notes."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete(messages, temperature=0.3, max_tokens=500)
        return result.content
