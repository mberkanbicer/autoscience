"""Export sandbox analysis runs as Jupyter notebooks."""

from __future__ import annotations

import json
from typing import Any


def build_notebook(
    *,
    title: str,
    script: str,
    stdout: str = "",
    stderr: str = "",
    artifacts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a nbformat 4 notebook from an analysis script and outputs."""
    cells: list[dict[str, Any]] = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [f"# {title}\n", "\n", "Exported from Autoscience sandbox.\n"],
        },
        {
            "cell_type": "code",
            "metadata": {},
            "source": script.splitlines(keepends=True) or ["# No script captured\n"],
            "outputs": [],
            "execution_count": 1,
        },
    ]

    if stdout.strip():
        cells.append({
            "cell_type": "code",
            "metadata": {},
            "source": ["# stdout\n"],
            "outputs": [
                {
                    "output_type": "stream",
                    "name": "stdout",
                    "text": stdout.splitlines(keepends=True),
                },
            ],
            "execution_count": None,
        })

    if stderr.strip():
        cells.append({
            "cell_type": "code",
            "metadata": {},
            "source": ["# stderr\n"],
            "outputs": [
                {
                    "output_type": "stream",
                    "name": "stderr",
                    "text": stderr.splitlines(keepends=True),
                },
            ],
            "execution_count": None,
        })

    if artifacts:
        artifact_lines = ["## Artifacts\n"] + [
            f"- **{a.get('artifact_type', 'file')}**: {a.get('description') or a.get('file_path', '')}\n"
            for a in artifacts
        ]
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": artifact_lines,
        })

    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "cells": cells,
    }


def notebook_to_json(notebook: dict[str, Any]) -> str:
    return json.dumps(notebook, indent=2)
