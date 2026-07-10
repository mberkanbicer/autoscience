"""Auto-number figures and tables in LaTeX exports."""

from __future__ import annotations

import re

_FIGURE_BLOCK = re.compile(r"\\begin\{figure\}.*?\\end\{figure\}", re.DOTALL)
_TABLE_BLOCK = re.compile(r"\\begin\{table\}.*?\\end\{table\}", re.DOTALL)
_CAPTION = re.compile(r"\\caption\{([^}]*)\}")


def _number_block(block: str, label: str, counter: int) -> str:
    prefix = f"{label} {counter}"
    if _CAPTION.search(block):
        return _CAPTION.sub(
            lambda m: f"\\caption{{{prefix}: {m.group(1).strip()}}}",
            block,
            count=1,
        )
    closing = f"\\end{{{label.lower()}}}"
    caption = f"\\caption{{{prefix}}}\n"
    return block.replace(closing, f"{caption}{closing}")


def number_figures_and_tables(latex: str) -> str:
    """Insert or prefix numbered captions for figure and table environments."""
    if not latex:
        return latex

    fig_num = 0

    def replace_figure(match: re.Match[str]) -> str:
        nonlocal fig_num
        fig_num += 1
        return _number_block(match.group(0), "Figure", fig_num)

    numbered = _FIGURE_BLOCK.sub(replace_figure, latex)

    table_num = 0

    def replace_table(match: re.Match[str]) -> str:
        nonlocal table_num
        table_num += 1
        return _number_block(match.group(0), "Table", table_num)

    return _TABLE_BLOCK.sub(replace_table, numbered)
