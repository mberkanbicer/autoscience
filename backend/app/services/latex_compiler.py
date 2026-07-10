"""Server-side LaTeX to PDF compilation."""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path

from app.engine.latex_numbering import number_figures_and_tables


async def compile_latex_to_pdf(
    latex: str,
    bibtex: str | None = None,
    *,
    auto_number: bool = True,
) -> tuple[bytes | None, str | None]:
    """Compile LaTeX to PDF using pdflatex when available."""
    if not shutil.which("pdflatex"):
        return None, "pdflatex is not installed on the server"

    content = number_figures_and_tables(latex) if auto_number else latex

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        tex_path = work / "main.tex"
        tex_path.write_text(content, encoding="utf-8")

        if bibtex:
            (work / "references.bib").write_text(bibtex, encoding="utf-8")

        cmd = [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-no-shell-escape",
            "main.tex",
        ]

        for _ in range(2):
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=work,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                err = stderr.decode(errors="replace")[-2000:]
                return None, f"pdflatex failed: {err}"

        pdf_path = work / "main.pdf"
        if not pdf_path.exists():
            return None, "pdflatex did not produce a PDF file"

        return pdf_path.read_bytes(), None
