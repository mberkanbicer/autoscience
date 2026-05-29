"""Keyword expansion and search planning engine."""

from dataclasses import dataclass, field
from typing import Any

import structlog

from ..llm.base import Message
from ..llm.router import LLMRouter

logger = structlog.get_logger()


@dataclass
class KeywordExpansion:
    """Expanded keywords from an idea."""

    core_concepts: list[str] = field(default_factory=list)
    synonyms: list[str] = field(default_factory=list)
    method_terms: list[str] = field(default_factory=list)
    application_terms: list[str] = field(default_factory=list)
    metric_terms: list[str] = field(default_factory=list)
    adjacent_field_terms: list[str] = field(default_factory=list)
    negative_terms: list[str] = field(default_factory=list)


@dataclass
class SearchQueryPlan:
    """A planned search query."""

    text: str
    query_type: str  # high_impact, frontier, review, contradiction, dataset, adjacent
    rationale: str
    year_from: int | None = None
    year_to: int | None = None
    limit: int = 20
    sort_by: str = "relevance"
    sources: list[str] = field(default_factory=list)


@dataclass
class SearchPlan:
    """Complete search plan for an idea."""

    idea: str
    keywords: KeywordExpansion
    queries: list[SearchQueryPlan] = field(default_factory=list)
    total_estimated_results: int = 0
    strategy_notes: str = ""


class KeywordExpansionEngine:
    """Engine for expanding ideas into search queries."""

    def __init__(self, llm_router: LLMRouter):
        self.llm = llm_router

    async def expand_keywords(self, idea: str, domain: str | None = None) -> KeywordExpansion:
        """Expand an idea into comprehensive keywords."""
        system = """You are a scientific keyword expansion expert.

Given a research idea, generate comprehensive keywords for academic literature search.

Output a JSON object with:
- core_concepts: Main concepts in the idea (3-5 terms)
- synonyms: Alternative terms for the same concepts (5-10 terms)
- method_terms: Research methods related to this idea (5-10 terms)
- application_terms: Application domains (3-5 terms)
- metric_terms: Evaluation metrics relevant to this idea (3-5 terms)
- adjacent_field_terms: Terms from related but distinct fields (5-8 terms)
- negative_terms: Terms to exclude from searches (2-3 terms)

Be specific and use domain-appropriate terminology."""

        user = f"""Research idea: {idea}
{f'Domain: {domain}' if domain else ''}

Generate comprehensive search keywords as JSON."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})

        data = result.data
        return KeywordExpansion(
            core_concepts=data.get("core_concepts", []),
            synonyms=data.get("synonyms", []),
            method_terms=data.get("method_terms", []),
            application_terms=data.get("application_terms", []),
            metric_terms=data.get("metric_terms", []),
            adjacent_field_terms=data.get("adjacent_field_terms", []),
            negative_terms=data.get("negative_terms", []),
        )

    async def create_search_plan(
        self,
        idea: str,
        domain: str | None = None,
        current_year: int = 2025,
    ) -> SearchPlan:
        """Create a comprehensive search plan for an idea."""
        # Step 1: Expand keywords
        keywords = await self.expand_keywords(idea, domain)

        # Step 2: Create search queries
        queries = await self._create_queries(idea, keywords, current_year)

        # Step 3: Create strategy notes
        strategy_notes = await self._create_strategy_notes(idea, keywords, queries)

        return SearchPlan(
            idea=idea,
            keywords=keywords,
            queries=queries,
            total_estimated_results=sum(q.limit for q in queries),
            strategy_notes=strategy_notes,
        )

    async def _create_queries(
        self,
        idea: str,
        keywords: KeywordExpansion,
        current_year: int,
    ) -> list[SearchQueryPlan]:
        """Create search queries from expanded keywords."""
        queries = []

        # Build base search terms
        core_terms = " ".join(keywords.core_concepts[:3])
        method_terms = " OR ".join(keywords.method_terms[:3])

        # Query 1: High-impact papers (last 5 years)
        queries.append(
            SearchQueryPlan(
                text=f"({core_terms})",
                query_type="high_impact",
                rationale="Find highly-cited foundational papers in the area",
                year_from=current_year - 5,
                year_to=current_year,
                limit=20,
                sort_by="citations",
            )
        )

        # Query 2: Frontier papers (last 12 months)
        queries.append(
            SearchQueryPlan(
                text=f"({core_terms})",
                query_type="frontier",
                rationale="Find recent cutting-edge developments",
                year_from=current_year - 1,
                year_to=current_year,
                limit=20,
                sort_by="date",
            )
        )

        # Query 3: Review/survey papers
        queries.append(
            SearchQueryPlan(
                text=f"({core_terms}) AND (review OR survey OR overview)",
                query_type="review",
                rationale="Find comprehensive reviews of the field",
                year_from=current_year - 3,
                year_to=current_year,
                limit=10,
                sort_by="citations",
            )
        )

        # Query 4: Method-specific search
        if keywords.method_terms:
            queries.append(
                SearchQueryPlan(
                    text=f"({core_terms}) AND ({method_terms})",
                    query_type="method",
                    rationale="Find papers using specific methods relevant to the idea",
                    year_from=current_year - 3,
                    year_to=current_year,
                    limit=15,
                    sort_by="relevance",
                )
            )

        # Query 5: Contradiction search
        queries.append(
            SearchQueryPlan(
                text=f"({core_terms}) AND (contradict OR challenge OR limitation OR failure)",
                query_type="contradiction",
                rationale="Find papers that reveal limitations or contradictions",
                year_from=current_year - 3,
                year_to=current_year,
                limit=10,
                sort_by="relevance",
            )
        )

        # Query 6: Dataset/benchmark papers
        if keywords.metric_terms:
            metric_terms = " OR ".join(keywords.metric_terms[:3])
            queries.append(
                SearchQueryPlan(
                    text=f"({core_terms}) AND ({metric_terms}) AND (benchmark OR dataset OR evaluation)",
                    query_type="dataset",
                    rationale="Find benchmark datasets and evaluation papers",
                    year_from=current_year - 3,
                    year_to=current_year,
                    limit=10,
                    sort_by="relevance",
                )
            )

        # Query 7: Adjacent field search
        if keywords.adjacent_field_terms:
            adjacent_terms = " OR ".join(keywords.adjacent_field_terms[:3])
            queries.append(
                SearchQueryPlan(
                    text=f"({adjacent_terms}) AND ({core_terms})",
                    query_type="adjacent",
                    rationale="Find cross-disciplinary connections",
                    year_from=current_year - 3,
                    year_to=current_year,
                    limit=10,
                    sort_by="relevance",
                )
            )

        # Query 8: Application-specific search
        if keywords.application_terms:
            app_terms = " OR ".join(keywords.application_terms[:2])
            queries.append(
                SearchQueryPlan(
                    text=f"({core_terms}) AND ({app_terms})",
                    query_type="application",
                    rationale="Find papers in specific application domains",
                    year_from=current_year - 3,
                    year_to=current_year,
                    limit=10,
                    sort_by="relevance",
                )
            )

        return queries

    async def _create_strategy_notes(
        self,
        idea: str,
        keywords: KeywordExpansion,
        queries: list[SearchQueryPlan],
    ) -> str:
        """Create strategy notes explaining the search approach."""
        system = """You are a research strategy documenter.

Given a research idea, keywords, and search queries, create a brief strategy note explaining:
1. The search approach
2. Why these queries were chosen
3. What each query type targets
4. Any search limitations or considerations

Keep it concise and actionable."""

        queries_summary = "\n".join(
            [f"- [{q.query_type}] {q.text} ({q.rationale})" for q in queries]
        )

        user = f"""Idea: {idea}

Core concepts: {', '.join(keywords.core_concepts)}
Method terms: {', '.join(keywords.method_terms)}
Adjacent fields: {', '.join(keywords.adjacent_field_terms)}

Search queries:
{queries_summary}

Create a brief search strategy note."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete(messages, temperature=0.3, max_tokens=500)
        return result.content

    def combine_search_terms(self, keywords: KeywordExpansion) -> str:
        """Combine keywords into a single search string."""
        terms = []
        if keywords.core_concepts:
            terms.append("(" + " OR ".join(keywords.core_concepts[:3]) + ")")
        if keywords.method_terms:
            terms.append("(" + " OR ".join(keywords.method_terms[:2]) + ")")
        return " AND ".join(terms) if terms else ""

    def estimate_query_complexity(self, query: str) -> int:
        """Estimate the complexity of a query (1-10)."""
        # Simple heuristic based on operators
        operators = ["AND", "OR", "NOT", "(", ")"]
        complexity = 1
        for op in operators:
            complexity += query.count(op)
        return min(complexity, 10)
