"""Generate and persist manuscripts from research run context."""

from __future__ import annotations

import asyncio
import io
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.latex_numbering import number_figures_and_tables
from app.engine.manuscript_engine import ManuscriptGenerator
from app.llm.router import LLMRouter
from app.models.report import Manuscript as ManuscriptModel

from .artifact_linking_service import ArtifactLinkingService
from .manuscript_context_service import ManuscriptContextService


class ManuscriptService:
    """Coordinates manuscript context, generation, persistence, and export."""

    def __init__(self, db: AsyncSession, llm_router: LLMRouter | None = None):
        self.db = db
        self.llm_router = llm_router
        self.context_service = ManuscriptContextService(db)
        self.artifact_linking = ArtifactLinkingService(db)

    async def generate_for_run(
        self,
        run_id: str,
        experiment_result: dict | None = None,
        claims: list[dict] | None = None,
    ) -> ManuscriptModel:
        """Generate or refresh the manuscript linked to a research run.

        After generation, builds cross-mode artifact links to persist the
        mapping between experiment artifacts and manuscript sections.

        Args:
            run_id: Research run to generate manuscript for.
            experiment_result: Optional in-memory experiment result from the
                workflow state. When provided, it is injected alongside the
                DB-persisted experiment data as a richer source of findings.
            claims: Optional structured claims extracted from experiment
                output via the results-to-claims pipeline.

        """
        run = await self.context_service.get_run(run_id)
        if not run:
            raise ValueError("Research run not found")

        if not self.llm_router:
            raise RuntimeError("LLM router is required for manuscript generation")

        params = await self.context_service.build_generation_params(
            run_id,
            experiment_result=experiment_result,
            claims=claims,
        )
        generator = ManuscriptGenerator(self.llm_router)
        manuscript_data = await generator.generate_manuscript(params)
        content_latex = ManuscriptGenerator.assemble_latex_document(manuscript_data)

        existing = await self._get_manuscript_for_run(run_id)
        if existing:
            existing.title = manuscript_data["title"]
            existing.content_latex = content_latex
            existing.bibtex = manuscript_data["references"]
            existing.version += 1
            await self.db.flush()
            await self.db.refresh(existing)
            manuscript = existing
        else:
            manuscript = ManuscriptModel(
                id=str(uuid4()),
                project_id=run.project_id,
                run_id=run_id,
                title=manuscript_data["title"],
                content_latex=content_latex,
                bibtex=manuscript_data["references"],
                status="draft",
            )
            self.db.add(manuscript)
            await self.db.flush()
            await self.db.refresh(manuscript)

        # Build cross-mode artifact links after generation
        try:
            # Extract effect sizes for linking from the experiment
            effect_size_refs = []
            if params.structured_effect_sizes:
                effect_size_refs = params.structured_effect_sizes

            # Build the experiment dict from params context
            experiment_for_linking = None
            if experiment_result:
                experiment_for_linking = experiment_result
            elif params.validation_results:
                experiment_for_linking = {
                    "success": any(v.get("result") == "completed" for v in params.validation_results),
                    "stdout": "\n".join(
                        v.get("result", "") for v in params.validation_results
                        if v.get("metric") == "experiment_output"
                    ),
                    "artifacts": params.experiment_artifacts,
                }

            await self.artifact_linking.build_links(
                manuscript_id=manuscript.id,
                experiment=experiment_for_linking,
                claims=claims,
                effect_sizes=effect_size_refs,
            )
        except (ValueError, KeyError, SQLAlchemyError) as exc:
            import structlog
            logger = structlog.get_logger()
            logger.warning("artifact_linking_data_error", manuscript_id=manuscript.id, error=str(exc))
        except Exception as exc:
            import structlog
            logger = structlog.get_logger()
            logger.warning("artifact_linking_failed", manuscript_id=manuscript.id, error=str(exc))

        return manuscript

    async def _get_manuscript_for_run(self, run_id: str) -> ManuscriptModel | None:
        result = await self.db.execute(
            select(ManuscriptModel)
            .where(ManuscriptModel.run_id == run_id)
            .order_by(ManuscriptModel.created_at.desc())
            .limit(1),
        )
        return result.scalar_one_or_none()

    @staticmethod
    def prepare_latex(manuscript: ManuscriptModel) -> str:
        """Return export-ready LaTeX with auto-numbered figures and tables."""
        return number_figures_and_tables(manuscript.content_latex or "")

    @staticmethod
    def export_bundle(manuscript: ManuscriptModel) -> bytes:
        """Create a zip archive with main.tex and references.bib."""
        buffer = io.BytesIO()
        latex = ManuscriptService.prepare_latex(manuscript)
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("main.tex", latex)
            archive.writestr("references.bib", manuscript.bibtex or "")
        return buffer.getvalue()

    @staticmethod
    def export_markdown(manuscript: ManuscriptModel) -> str:
        """Convert LaTeX manuscript content to Markdown.

        This is a best-effort conversion that handles common LaTeX constructs.
        """
        latex = manuscript.content_latex or ""

        # Remove LaTeX preamble
        md = latex.split("\\begin{document}", 1)[-1] if "\\begin{document}" in latex else latex
        md = md.split("\\end{document}", 1)[0] if "\\end{document}" in md else md

        # Title, author, date
        md = re.sub(r"\\title\{([^}]*)\}", r"# \1\n", md)
        md = re.sub(r"\\author\{([^}]*)\}", r"*\1*\n", md)
        md = re.sub(r"\\date\{([^}]*)\}", r"*\1*\n", md)

        # Sections
        md = re.sub(r"\\section\{([^}]*)\}", r"## \1", md)
        md = re.sub(r"\\subsection\{([^}]*)\}", r"### \1", md)
        md = re.sub(r"\\subsubsection\{([^}]*)\}", r"#### \1", md)

        # Abstract environment
        md = re.sub(r"\\begin\{abstract\}", "", md)
        md = re.sub(r"\\end\{abstract\}", "", md)

        # Text formatting
        md = re.sub(r"\\textbf\{([^}]*)\}", r"**\1**", md)
        md = re.sub(r"\\textit\{([^}]*)\}", r"*\1*", md)
        md = re.sub(r"\\emph\{([^}]*)\}", r"*\1*", md)
        md = re.sub(r"\\underline\{([^}]*)\}", r"__\1__", md)

        # Lists
        md = re.sub(r"\\begin\{itemize\}", "", md)
        md = re.sub(r"\\end\{itemize\}", "", md)
        md = re.sub(r"\\item", "- ", md)
        md = re.sub(r"\\begin\{enumerate\}", "", md)
        md = re.sub(r"\\end\{enumerate\}", "", md)

        # Citations and references
        md = re.sub(r"\\cite\{([^}]*)\}", r"[@\1]", md)
        md = re.sub(r"\\citet\{([^}]*)\}", r"@\1", md)
        md = re.sub(r"\\citep\{([^}]*)\}", r"[@\1]", md)

        # Figure placeholders
        md = re.sub(r"\\begin\{figure\}(.*?)\\end\{figure\}", r"*[Figure]\1*", md, flags=re.DOTALL)
        md = re.sub(r"\\includegraphics(?:\[.*?\])?\{([^}]*)\}", r"![\1](\1)", md)
        md = re.sub(r"\\caption\{([^}]*)\}", r"**\1**", md)

        # Tables
        md = re.sub(r"\\begin\{table\}(.*?)\\end\{table\}", r"*[Table]\1*", md, flags=re.DOTALL)
        md = re.sub(r"\\begin\{tabular\}(.*?)\\end\{tabular\}", r"\n```\n\n```\n", md, flags=re.DOTALL)

        # Math
        md = re.sub(r"\\\[(.*?)\\\]", r"$$\1$$", md, flags=re.DOTALL)
        md = re.sub(r"\\\((.*?)\\\)", r"$\1$", md, flags=re.DOTALL)

        # Remove remaining LaTeX commands
        md = re.sub(r"\\[a-zA-Z]+(?:\[.*?\])?\{[^}]*\}\s*", "", md)
        md = re.sub(r"\\[a-zA-Z]+(?:\[.*?\])?", "", md)

        # Environments
        md = re.sub(r"\\begin\{[a-zA-Z]*\}", "", md)
        md = re.sub(r"\\end\{[a-zA-Z]*\}", "", md)

        # Multiple blank lines -> single blank line
        md = re.sub(r"\n{3,}", "\n\n", md)
        md = re.sub(r"\\maketitle", "", md)
        md = re.sub(r"\\bibliographystyle\{[^}]*\}", "", md)
        md = re.sub(r"\\bibliography\{[^}]*\}", "", md)
        md = re.sub(r"\\documentclass(?:\[.*?\])?\{[^}]*\}", "", md)
        md = re.sub(r"\\usepackage(?:\[.*?\])?\{[^}]*\}", "", md)

        return md.strip()

    @staticmethod
    def export_html(manuscript: ManuscriptModel) -> str:
        """Convert manuscript content to styled HTML."""
        md = ManuscriptService.export_markdown(manuscript)

        # Simple Markdown-to-HTML conversion
        html_parts: list[str] = []
        in_code_block = False

        for line in md.split("\n"):
            if line.startswith("```"):
                in_code_block = not in_code_block
                if in_code_block:
                    html_parts.append('<pre class="code-block"><code>')
                else:
                    html_parts.append("</code></pre>")
                continue

            if in_code_block:
                html_parts.append(line + "\n")
                continue

            if not line.strip():
                html_parts.append("<br/>")
                continue

            # Headings
            if line.startswith("# "):
                html_parts.append(f"<h1>{line[2:].strip()}</h1>")
            elif line.startswith("## "):
                html_parts.append(f"<h2>{line[3:].strip()}</h2>")
            elif line.startswith("### "):
                html_parts.append(f"<h3>{line[4:].strip()}</h3>")
            elif line.startswith("#### "):
                html_parts.append(f"<h4>{line[5:].strip()}</h4>")
            elif line.startswith("- "):
                html_parts.append(f"<li>{line[2:].strip()}</li>")
            elif line.startswith("["):
                html_parts.append(f"<p class='figure-placeholder'>{line}</p>")
            else:
                html_parts.append(f"<p>{line}</p>")

        body = "\n".join(html_parts)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{manuscript.title or 'Untitled'}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Georgia', 'Times New Roman', serif; font-size: 16px; line-height: 1.8; color: #1a1a1a; max-width: 900px; margin: 0 auto; padding: 40px 24px; background: #fff; }}
  h1 {{ font-size: 28px; margin: 32px 0 16px; font-weight: 700; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; }}
  h2 {{ font-size: 22px; margin: 28px 0 12px; font-weight: 600; color: #2d3748; }}
  h3 {{ font-size: 18px; margin: 24px 0 8px; font-weight: 600; }}
  h4 {{ font-size: 16px; margin: 20px 0 8px; font-weight: 600; font-style: italic; }}
  p {{ margin: 12px 0; text-align: justify; }}
  li {{ margin: 4px 0 4px 24px; list-style-type: disc; }}
  .figure-placeholder {{ font-family: monospace; font-size: 14px; background: #f7fafc; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0; color: #718096; }}
  .code-block {{ display: block; background: #1a202c; color: #e2e8f0; padding: 16px; border-radius: 8px; font-size: 14px; overflow-x: auto; margin: 16px 0; }}
  br {{ display: block; content: ""; margin: 8px 0; }}
  @media (max-width: 640px) {{ body {{ padding: 20px 12px; font-size: 15px; }} h1 {{ font-size: 24px; }} }}
</style>
</head>
<body>
{body}
</body>
</html>
"""

    @staticmethod
    async def export_docx(manuscript: ManuscriptModel) -> tuple[bytes | None, str | None]:
        """Convert manuscript LaTeX to DOCX using pandoc when available.

        Returns (docx_bytes, error_message).
        """
        pandoc = shutil.which("pandoc")
        if not pandoc:
            return None, "pandoc is not installed on the server"

        latex = ManuscriptService.prepare_latex(manuscript)

        # Write LaTeX to temp file, convert via pandoc
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tex", delete=False, encoding="utf-8",
        ) as tex_file:
            tex_file.write(latex)
            tex_path = tex_file.name

        if manuscript.bibtex:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".bib", delete=False, encoding="utf-8",
            ) as bib_file:
                bib_file.write(manuscript.bibtex)
                bib_path = bib_file.name
        else:
            bib_path = None

        docx_path = tex_path.replace(".tex", ".docx")

        try:
            cmd = [pandoc, tex_path, "-o", docx_path, "--from", "latex", "--to", "docx"]
            if bib_path:
                cmd.extend(["--bibliography", bib_path])

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                err = stderr.decode(errors="replace")[-2000:]
                return None, f"pandoc failed: {err}"

            docx_bytes = Path(docx_path).read_bytes()
            return docx_bytes, None
        except (TimeoutError, FileNotFoundError, OSError) as exc:
            return None, f"DOCX conversion error: {exc}"
        except Exception as exc:
            return None, f"DOCX conversion unexpected error: {exc}"
        finally:
            Path(tex_path).unlink(missing_ok=True)
            if bib_path:
                Path(bib_path).unlink(missing_ok=True)
            Path(docx_path).unlink(missing_ok=True)
