"""Tests for LaTeX figure/table auto-numbering."""

from app.engine.latex_numbering import number_figures_and_tables


def test_numbers_figures_and_tables():
    latex = r"""
\begin{figure}
\includegraphics{plot.png}
\end{figure}
\begin{table}
\begin{tabular}{cc}
A & B \\
\end{tabular}
\end{table}
"""
    result = number_figures_and_tables(latex)
    assert r"\caption{Figure 1}" in result
    assert r"\caption{Table 1}" in result


def test_prefixes_existing_captions():
    latex = r"""
\begin{figure}
\caption{Results overview}
\end{figure}
"""
    result = number_figures_and_tables(latex)
    assert r"\caption{Figure 1: Results overview}" in result