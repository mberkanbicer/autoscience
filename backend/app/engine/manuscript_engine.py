"""Manuscript generation engine for IMRaD structure."""

from dataclasses import dataclass, field
from typing import Any

import structlog

from app.llm.base import Message
from app.llm.router import LLMRouter

logger = structlog.get_logger()


@dataclass
class ManuscriptSection:
    """A section of a scientific manuscript."""

    title: str
    content: str
    word_count: int = 0


@dataclass
class ManuscriptGenerationParams:
    """Parameters for manuscript generation."""

    idea_text: str
    problem_statement: str | None = None
    method_description: str | None = None
    findings: list[str] = field(default_factory=list)
    papers: list[dict[str, Any]] = field(default_factory=list)
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    validation_results: list[dict[str, Any]] = field(default_factory=list)
    target_journal: str | None = None
    section_style: str = "IMRaD"  # IMRaD or standard
    # Cross-mode artifact references: structured info about experiment artifacts
    # that can be referenced explicitly in each section.
    experiment_artifacts: list[dict[str, Any]] = field(default_factory=list)
    structured_claims: list[dict[str, Any]] = field(default_factory=list)
    structured_effect_sizes: list[dict[str, Any]] = field(default_factory=list)


class ManuscriptGenerator:
    """Generates scientific manuscripts in IMRaD format."""

    def __init__(self, llm_router: LLMRouter):
        self.llm = llm_router

    async def generate_manuscript(
        self,
        params: ManuscriptGenerationParams,
    ) -> dict[str, Any]:
        """Generate a complete scientific manuscript."""
        # Generate each section
        introduction = await self._generate_introduction(params)
        methods = await self._generate_methods(params)
        results = await self._generate_results(params)
        discussion = await self._generate_discussion(params)
        references = await self._generate_references(params.papers)

        # Assemble manuscript
        manuscript = {
            "title": await self._generate_title(params),
            "abstract": await self._generate_abstract(introduction, methods, results, discussion),
            "sections": [
                {"title": "1. Introduction", "content": introduction.content},
                {"title": "2. Methods", "content": methods.content},
                {"title": "3. Results", "content": results.content},
                {"title": "4. Discussion", "content": discussion.content},
            ],
            "references": references,
        }

        return manuscript

    @staticmethod
    def citation_key(paper: dict[str, Any]) -> str:
        """Stable BibTeX key for a paper record."""
        paper_id = str(paper.get("id") or "paper")
        year = paper.get("year") or "nd"
        return f"paper_{paper_id[:8]}_{year}"

    @staticmethod
    def assemble_latex_document(manuscript_data: dict[str, Any]) -> str:
        """Wrap generated sections in a compilable LaTeX document."""
        title = manuscript_data.get("title", "Untitled Study")
        abstract = manuscript_data.get("abstract", "")
        sections = manuscript_data.get("sections", [])

        body = "\n\n".join(
            f"\\section{{{section['title'].split('. ', 1)[-1]}}}\n{section['content']}"
            for section in sections
        )

        return f"""\\documentclass[11pt]{{article}}
\\usepackage{{graphicx}}
\\usepackage{{hyperref}}
\\usepackage{{natbib}}

\\title{{{title}}}
\\author{{Autoscience Research Studio}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle

\\begin{{abstract}}
{abstract}
\\end{{abstract}}

{body}

\\bibliographystyle{{plainnat}}
\\bibliography{{references}}

\\end{{document}}
"""

    async def _generate_title(self, params: ManuscriptGenerationParams) -> str:
        """Generate a concise, informative title."""
        system = """You are a scientific editor. Generate a concise, informative title (12-15 words max) for this research.

The title should:
1. State the key finding or question
2. Identify the system/context studied
3. Be specific and searchable

Output only the title text, no quotes or formatting."""

        user = f"""Research idea: {params.idea_text}

Key findings: {chr(10).join(f'- {f}' for f in params.findings[:5])}

Hypotheses tested: {chr(10).join(f'- {h.get("statement", "")}' for h in params.hypotheses[:3])}"""

        messages = [Message(role="system", content=system), Message(role="user", content=user)]
        result = await self.llm.complete(messages, temperature=0.3, max_tokens=100)
        return result.content.strip()

    async def _generate_abstract(
        self,
        introduction: ManuscriptSection,
        methods: ManuscriptSection,
        results: ManuscriptSection,
        discussion: ManuscriptSection,
    ) -> str:
        """Generate an abstract from the other sections."""
        system = """You are a scientific editor. Write a concise abstract (200-250 words) based on the provided sections.

Structure:
- Background (1-2 sentences)
- Methods (1-2 sentences)
- Results (2-3 sentences)
- Conclusions (1-2 sentences)

Write in clear, declarative prose without citations in the abstract."""

        user = f"""Introduction (first paragraph):
{introduction.content[:500]}

Methods (first paragraph):
{methods.content[:500]}

Results (first paragraph):
{results.content[:500]}

Discussion (first paragraph):
{discussion.content[:500]}"""

        messages = [Message(role="system", content=system), Message(role="user", content=user)]
        result = await self.llm.complete(messages, temperature=0.3, max_tokens=300)
        return result.content.strip()

    async def _generate_introduction(self, params: ManuscriptGenerationParams) -> ManuscriptSection:
        """Generate the introduction section."""
        system = """You are a scientific writer. Write the Introduction section (800-1200 words) for a scientific manuscript.

Structure:
1. Background - Establish context and importance of the topic
2. Prior Work - Summarize key existing research (cite specific papers)
3. Gap - Identify what is unknown or unresolved
4. Contribution - What this work adds
5. Approach - Brief preview of methodology

Use LaTeX-style citations where appropriate: \\cite{author2024} or \\cite{paper_doi}.

Write in academic tone, use precise language."""

        context = f"""Research Idea: {params.idea_text}

Papers to cite in introduction:
{chr(10).join(f'- {p.get("title", "")} ({p.get("year", "")})' for p in params.papers[:10])}"""

        user = f"""Write the Introduction section for this research:

{context}

Include citations to relevant papers. Focus on the scientific context and research gap."""

        messages = [Message(role="system", content=system), Message(role="user", content=user)]
        result = await self.llm.complete(messages, temperature=0.4, max_tokens=1500)

        return ManuscriptSection(title="Introduction", content=result.content)

    async def _generate_methods(self, params: ManuscriptGenerationParams) -> ManuscriptSection:
        """Generate the methods section."""
        system = """You are a scientific methods writer. Write the Methods section (1000-1500 words).

Structure:
1. Overall approach
2. Data sources and preparation
3. Experimental design
4. Statistical methods
5. Software/tools used

Be detailed enough for reproduction. Use LaTeX-style citations: \\cite{method_paper}.
Use code blocks or algorithmic descriptions where appropriate."""

        hypotheses_text = chr(10).join(
            f'- Hypothesis: {h.get("statement", "")}'
            for h in params.hypotheses
        ) if params.hypotheses else "No specific hypotheses"

        user = f"""Write the Methods section based on:

Idea: {params.idea_text}

Method description: {params.method_description or 'To be determined from literature analysis'}

Hypotheses:
{hypotheses_text}

Focus on reproducibility and clarity."""

        messages = [Message(role="system", content=system), Message(role="user", content=user)]
        result = await self.llm.complete(messages, temperature=0.3, max_tokens=1500)

        return ManuscriptSection(title="Methods", content=result.content)

    async def _generate_results(self, params: ManuscriptGenerationParams) -> ManuscriptSection:
        """Generate the results section."""
        system = """You are a scientific results writer. Write the Results section (1200-2000 words).

Structure:
1. Key findings with quantitative support
2. Statistical test results
3. Visualizations (describe figures/tables)
4. Comparison with prior work

Present data objectively. Use LaTeX-style citations where you reference other work.
For figures, use placeholders like: [Figure 1: Description of visualization]

Present numerical results clearly with units and significance."""

        findings_text = chr(10).join(params.findings) if params.findings else "Analysis pending"
        validation_text = chr(10).join(
            f'- {v.get("metric", "")}: {v.get("result", "")} (p={v.get("p_value", "N/A")})'
            for v in params.validation_results
        ) if params.validation_results else "Experimental results to be added"

        # Build structured artifact references for the Results section
        artifact_refs = ""
        if params.experiment_artifacts:
            figures = [a for a in params.experiment_artifacts if a.get("artifact_type") == "figure"]
            tables = [a for a in params.experiment_artifacts if a.get("artifact_type") == "table"]
            if figures:
                artifact_refs += "\nFigures generated from experiment:\n"
                for f in figures:
                    desc = f.get("description", "Figure")[:150]
                    artifact_refs += f"- [Figure: {desc}]\n"
            if tables:
                artifact_refs += "\nTables generated from experiment:\n"
                for t in tables:
                    desc = t.get("description", "Table")[:150]
                    artifact_refs += f"- [Table: {desc}]\n"

        # Build effect size references
        es_refs = ""
        if params.structured_effect_sizes:
            es_refs += "\nEffect sizes measured:\n"
            for es in params.structured_effect_sizes:
                label = es.get("label", es.get("effect_type", "d"))
                value = es.get("value", "?")
                interp = es.get("interpretation", "").replace("_", " ")
                es_refs += f"- {label} = {value} ({interp} effect)\n"

        # Build structured claims
        claim_refs = ""
        if params.structured_claims:
            stat_claims = [c for c in params.structured_claims if c.get("claim_type") in ("statistical", "finding")]
            if stat_claims:
                claim_refs += "\nQuantitative findings:\n"
                for c in stat_claims[:8]:
                    statement = c.get("statement", "")[:200]
                    conf = c.get("confidence", 0.5)
                    claim_refs += f"- {statement} (confidence: {conf:.0%})\n"

        user = f"""Write the Results section based on:

Findings from literature analysis:
{findings_text}

Validation experiment results:
{validation_text}
{artifact_refs}
{es_refs}
{claim_refs}

Reference the specific figures, tables, effect sizes, and claims above in your results narrative."""

        messages = [Message(role="system", content=system), Message(role="user", content=user)]
        result = await self.llm.complete(messages, temperature=0.3, max_tokens=2000)

        return ManuscriptSection(title="Results", content=result.content)

    async def _generate_discussion(self, params: ManuscriptGenerationParams) -> ManuscriptSection:
        """Generate the discussion section."""
        system = """You are a scientific discussion writer. Write the Discussion section (1500-2500 words).

Structure:
1. Interpretation of key findings
2. Comparison with prior work
3. Limitations of the study
4. Implications for practice/theory
5. Future directions
6. Conclusions

Acknowledge limitations honestly. Reference prior work with citations: \\cite{author2024}."""

        user = f"""Write the Discussion section for this research:

Research Idea: {params.idea_text}

Key Findings:
{chr(10).join(f'- {f}' for f in params.findings[:10])}

Include thoughtful discussion of limitations and future work."""

        messages = [Message(role="system", content=system), Message(role="user", content=user)]
        result = await self.llm.complete(messages, temperature=0.4, max_tokens=2500)

        return ManuscriptSection(title="Discussion", content=result.content)

    async def _generate_references(self, papers: list[dict[str, Any]]) -> str:
        """Generate BibTeX bibliography."""
        bib_entries = []

        for paper in papers:
            bib_entries.append(
                CitationManager.generate_bibtex(
                    authors=paper.get("authors", []) if isinstance(paper.get("authors"), list) else [],
                    title=paper.get("title", ""),
                    year=paper.get("year", "n.d."),
                    venue=paper.get("venue", "Unknown Venue"),
                    doi=paper.get("doi"),
                    paper_id=self.citation_key(paper),
                ),
            )

        return "\n\n".join(bib_entries)


class CitationManager:
    """Manages citations and bibliographies."""

    @staticmethod
    def generate_bibtex(
        authors: list[str],
        title: str,
        year: int | str,
        venue: str,
        doi: str | None = None,
        paper_id: str | None = None,
    ) -> str:
        """Generate a BibTeX entry."""
        key = f"{paper_id or 'paper'}_{year}"

        entry = f"""@article{{{key},
  author = {{{" and ".join(authors[:10])}}},
  title = {{{title}}},
  journal = {{{venue}}},
  year = {{{year}}}
"""

        if doi:
            entry += f"  doi = {{{doi}}}\n"

        entry += "}"

        return entry

    @staticmethod
    def format_citation(
        paper: dict[str, Any],
        style: str = "APA",
    ) -> str:
        """Format a citation in the specified style."""
        authors = paper.get("authors", [])
        title = paper.get("title", "")
        year = paper.get("year", "n.d.")
        venue = paper.get("venue", "")

        if style == "APA":
            author_str = ", ".join(authors[:2])
            if len(authors) > 2:
                author_str += ", et al."
            return f"{author_str} ({year}). {title}. {venue}."

        if style == "IEEE":
            author_str = ", ".join(authors[:3])
            if len(authors) > 3:
                author_str += ","
            return f'[{year}] {author_str}, "{title}", {venue}.'

        if style == "Chicago":
            author_str = ", ".join(authors[:3])
            return f'{author_str}. {year}. "{title}." {venue}.'

        return f"{title} ({year})"
