"""Paper analysis engine for extracting structured information from papers."""

from dataclasses import dataclass, field
from typing import Any

import structlog

from app.llm.base import Message
from app.llm.router import LLMRouter

logger = structlog.get_logger()


@dataclass
class Claim:
    """A claim extracted from a paper."""

    text: str
    type: str  # finding, method, limitation, assumption
    confidence: float = 0.5
    evidence: str = ""


@dataclass
class PaperAnalysisResult:
    """Structured analysis of a paper."""

    paper_id: str
    problem: str = ""
    method: str = ""
    dataset_sample: str = ""
    metrics: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    future_work: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    key_claims: list[Claim] = field(default_factory=list)
    relation_to_idea: str = ""
    confidence: float = 0.0
    analysis_notes: str = ""


class PaperAnalysisEngine:
    """Engine for analyzing papers and extracting structured information."""

    def __init__(self, llm_router: LLMRouter):
        self.llm = llm_router

    async def analyze_paper(
        self,
        paper_id: str,
        title: str,
        abstract: str,
        idea_context: str,
        full_text: str | None = None,
    ) -> PaperAnalysisResult:
        """Analyze a paper and extract structured information."""
        # Use full text if available, otherwise abstract
        text_to_analyze = full_text or abstract

        if not text_to_analyze:
            return PaperAnalysisResult(
                paper_id=paper_id,
                confidence=0.0,
                analysis_notes="No text available for analysis",
            )

        # Extract structured information
        extraction = await self._extract_information(
            title=title,
            text=text_to_analyze,
            idea_context=idea_context,
        )

        # Extract claims
        claims = await self._extract_claims(
            title=title,
            text=text_to_analyze,
        )

        # Analyze relation to idea
        relation = await self._analyze_relation(
            title=title,
            text=text_to_analyze,
            idea_context=idea_context,
            findings=extraction.get("findings", []),
        )

        # Calculate confidence
        confidence = self._calculate_confidence(
            has_abstract=bool(abstract),
            has_full_text=bool(full_text),
            text_length=len(text_to_analyze),
        )

        return PaperAnalysisResult(
            paper_id=paper_id,
            problem=extraction.get("problem", ""),
            method=extraction.get("method", ""),
            dataset_sample=extraction.get("dataset_sample", ""),
            metrics=extraction.get("metrics", []),
            findings=extraction.get("findings", []),
            limitations=extraction.get("limitations", []),
            future_work=extraction.get("future_work", []),
            assumptions=extraction.get("assumptions", []),
            key_claims=[Claim(**c) if isinstance(c, dict) else c for c in claims],
            relation_to_idea=relation,
            confidence=confidence,
            analysis_notes=f"Analyzed {'full text' if full_text else 'abstract only'}",
        )

    async def _extract_information(
        self,
        title: str,
        text: str,
        idea_context: str,
    ) -> dict[str, Any]:
        """Extract structured information from paper text."""
        system = """You are a scientific paper analyst.

Extract structured information from the paper text.

Output a JSON object with:
- problem: The research problem addressed (string)
- method: The method or approach used (string)
- dataset_sample: The dataset or sample used (string)
- metrics: List of metrics reported (array of strings)
- findings: List of key findings (array of strings)
- limitations: List of limitations acknowledged (array of strings)
- future_work: List of future work directions (array of strings)
- assumptions: List of key assumptions (array of strings)

Be precise and extract only what is explicitly stated."""

        user = f"""Paper: {title}

Text:
{text[:4000]}

Idea context: {idea_context}

Extract structured information as JSON."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})
        return result.data

    async def _extract_claims(
        self,
        title: str,
        text: str,
    ) -> list[dict[str, Any]]:
        """Extract key claims from paper text."""
        system = """You are a scientific claim extractor.

Identify the key claims made in this paper.

Output a JSON object with:
- claims: Array of claim objects, each with:
  - text: The claim statement (string)
  - type: "finding" | "method" | "limitation" | "assumption" (string)
  - confidence: Your confidence in this claim 0-1 (float)
  - evidence: The evidence or reasoning supporting this claim (string)

Focus on the most important and specific claims."""

        user = f"""Paper: {title}

Text:
{text[:3000]}

Extract key claims as JSON."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})
        return result.data.get("claims", [])

    async def _analyze_relation(
        self,
        title: str,
        text: str,
        idea_context: str,
        findings: list[str],
    ) -> str:
        """Analyze how the paper relates to the given idea."""
        system = """You are a research relevance analyst.

Analyze how this paper relates to the given research idea.

Consider:
1. Does it address the same problem?
2. Does it use similar methods?
3. Does it provide evidence for or against the idea?
4. Does it identify gaps that the idea could fill?
5. Does it propose competing approaches?

Provide a brief, specific analysis (2-3 sentences)."""

        findings_text = "\n".join([f"- {f}" for f in findings[:5]]) if findings else "Not specified"

        user = f"""Paper: {title}

Key findings:
{findings_text}

Research idea: {idea_context}

Analyze the relationship between this paper and the idea."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete(messages, temperature=0.3, max_tokens=300)
        return result.content

    def _calculate_confidence(
        self,
        has_abstract: bool,
        has_full_text: bool,
        text_length: int,
    ) -> float:
        """Calculate analysis confidence based on available information."""
        confidence = 0.0

        if has_abstract:
            confidence += 0.3
        if has_full_text:
            confidence += 0.4

        # Text length factor
        if text_length > 5000:
            confidence += 0.2
        elif text_length > 2000:
            confidence += 0.15
        elif text_length > 500:
            confidence += 0.1

        return min(confidence, 1.0)

    async def batch_analyze(
        self,
        papers: list[dict[str, str]],
        idea_context: str,
    ) -> list[PaperAnalysisResult]:
        """Analyze multiple papers."""
        results = []

        for paper in papers:
            try:
                result = await self.analyze_paper(
                    paper_id=paper.get("id", ""),
                    title=paper.get("title", ""),
                    abstract=paper.get("abstract", ""),
                    idea_context=idea_context,
                    full_text=paper.get("full_text"),
                )
                results.append(result)
            except (ValueError, RuntimeError, KeyError) as e:
                logger.error(
                    "paper_analysis_error",
                    paper_id=paper.get("id"),
                    error=str(e),
                )
            except Exception as e:
                logger.error(
                    "paper_analysis_failed",
                    paper_id=paper.get("id"),
                    error=str(e),
                )
                # Add empty result for failed analysis
                results.append(
                    PaperAnalysisResult(
                        paper_id=paper.get("id", ""),
                        confidence=0.0,
                        analysis_notes=f"Analysis failed: {e!s}",
                    ),
                )

        return results

    async def compare_papers(
        self,
        analyses: list[PaperAnalysisResult],
    ) -> dict[str, Any]:
        """Compare multiple paper analyses."""
        if len(analyses) < 2:
            return {"error": "Need at least 2 papers to compare"}

        papers_summary = "\n".join(
            [
                f"Paper {i+1}: {a.paper_id}\n"
                f"Method: {a.method}\n"
                f"Findings: {', '.join(a.findings[:3])}"
                for i, a in enumerate(analyses[:5])
            ],
        )

        system = """You are a scientific comparison analyst.

Compare these paper analyses and identify:
1. Common themes
2. Contradictions
3. Complementary findings
4. Methodological differences
5. Research gaps

Output a JSON object with:
- common_themes: Array of common themes
- contradictions: Array of contradictions
- complementary_findings: Array of complementary findings
- methodological_differences: Array of differences
- research_gaps: Array of gaps"""

        user = f"""Paper analyses:
{papers_summary}

Compare these papers and identify patterns."""

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

        result = await self.llm.complete_structured(messages, schema={})
        return result.data
