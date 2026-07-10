"""Tests for Jupyter notebook export."""

from app.services.notebook_export_service import build_notebook, notebook_to_json


def test_build_notebook_structure():
    notebook = build_notebook(
        title="Test Experiment",
        script="print('hello')",
        stdout="hello\n",
        stderr="",
        artifacts=[{"artifact_type": "figure", "description": "plot.png"}],
    )
    assert notebook["nbformat"] == 4
    assert len(notebook["cells"]) >= 3
    assert notebook["cells"][0]["cell_type"] == "markdown"

    exported = notebook_to_json(notebook)
    assert "Test Experiment" in exported