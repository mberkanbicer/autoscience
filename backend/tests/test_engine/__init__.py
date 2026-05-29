"""Tests for deduplication and literature retrieval."""

import pytest

from app.connectors.base import RawPaper
from app.engine.deduplication import (
    normalize_title,
    normalize_doi,
    titles_are_similar,
    deduplicate_papers,
    select_papers_for_analysis,
    group_papers_by_type,
    group_papers_by_year,
)


def test_normalize_title():
    """Test title normalization."""
    assert normalize_title("The Quick Brown Fox") == "quick brown fox"
    assert normalize_title("A Simple Test.") == "simple test"
    assert normalize_title("") == ""
    assert normalize_title("Paper (2024)") == "paper 2024"


def test_normalize_doi():
    """Test DOI normalization."""
    assert normalize_doi("10.1234/test") == "10.1234/test"
    assert normalize_doi("https://doi.org/10.1234/test") == "10.1234/test"
    assert normalize_doi("HTTP://DOI.ORG/10.1234/TEST") == "10.1234/test"
    assert normalize_doi(None) is None
    assert normalize_doi("") is None


def test_titles_are_similar():
    """Test title similarity comparison."""
    assert titles_are_similar(
        "Machine Learning for Science",
        "Machine Learning for Science",
    )
    assert titles_are_similar(
        "A Study of Machine Learning",
        "Study of Machine Learning",
    )
    assert not titles_are_similar(
        "Machine Learning for Science",
        "Deep Learning for Vision",
    )


def test_deduplicate_papers():
    """Test paper deduplication."""
    papers = [
        RawPaper(
            source="source1",
            source_id="1",
            title="Paper A",
            doi="10.1234/a",
            authors=["Author 1"],
        ),
        RawPaper(
            source="source2",
            source_id="2",
            title="Paper A",  # Same title
            doi="10.1234/a",  # Same DOI
            authors=["Author 2"],
            citation_count=100,
        ),
        RawPaper(
            source="source1",
            source_id="3",
            title="Paper B",
            doi="10.1234/b",
            authors=["Author 3"],
        ),
    ]

    deduplicated = deduplicate_papers(papers)

    assert len(deduplicated) == 2
    # First paper should have merged metadata
    assert deduplicated[0].citation_count == 100
    assert len(deduplicated[0].authors) == 2


def test_select_papers_for_analysis():
    """Test paper selection for analysis."""
    papers = [
        RawPaper(
            source="source",
            source_id="1",
            title="High Impact Paper",
            citation_count=500,
            year=2024,
            abstract="Abstract present",
        ),
        RawPaper(
            source="source",
            source_id="2",
            title="Low Impact Paper",
            citation_count=5,
            year=2020,
        ),
        RawPaper(
            source="source",
            source_id="3",
            title="Recent Paper",
            citation_count=50,
            year=2025,
            abstract="Recent abstract",
        ),
    ]

    selected = select_papers_for_analysis(papers, max_papers=2)

    assert len(selected) == 2
    # Should be sorted by relevance
    assert selected[0].title in ["High Impact Paper", "Recent Paper"]


def test_select_papers_with_filters():
    """Test paper selection with filters."""
    papers = [
        RawPaper(
            source="source",
            source_id="1",
            title="Paper with Abstract",
            abstract="This is an abstract",
        ),
        RawPaper(
            source="source",
            source_id="2",
            title="Paper without Abstract",
        ),
    ]

    selected = select_papers_for_analysis(papers, require_abstract=True)
    assert len(selected) == 1
    assert selected[0].title == "Paper with Abstract"


def test_group_papers_by_type():
    """Test grouping papers by type."""
    papers = [
        RawPaper(source="s", source_id="1", title="Research", paper_type="research"),
        RawPaper(source="s", source_id="2", title="Review", paper_type="review"),
        RawPaper(source="s", source_id="3", title="Another Research", paper_type="research"),
    ]

    groups = group_papers_by_type(papers)

    assert len(groups["research"]) == 2
    assert len(groups["review"]) == 1


def test_group_papers_by_year():
    """Test grouping papers by year."""
    papers = [
        RawPaper(source="s", source_id="1", title="2024 Paper", year=2024),
        RawPaper(source="s", source_id="2", title="2023 Paper", year=2023),
        RawPaper(source="s", source_id="3", title="2024 Paper 2", year=2024),
    ]

    groups = group_papers_by_year(papers)

    assert len(groups[2024]) == 2
    assert len(groups[2023]) == 1


def test_deduplicate_empty_list():
    """Test deduplication with empty list."""
    assert deduplicate_papers([]) == []


def test_deduplicate_single_paper():
    """Test deduplication with single paper."""
    papers = [
        RawPaper(source="s", source_id="1", title="Only Paper"),
    ]
    assert len(deduplicate_papers(papers)) == 1
