"""Paper deduplication and normalization utilities."""

import re
from difflib import SequenceMatcher
from typing import Any

from ..connectors.base import RawPaper


def normalize_title(title: str) -> str:
    """Normalize a paper title for comparison."""
    if not title:
        return ""

    # Lowercase
    normalized = title.lower()

    # Remove special characters except spaces and alphanumeric
    normalized = re.sub(r"[^a-z0-9\s]", "", normalized)

    # Remove extra whitespace
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # Remove common words that don't affect similarity
    stop_words = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "with", "by"}
    words = normalized.split()
    words = [w for w in words if w not in stop_words]

    return " ".join(words)


def normalize_doi(doi: str | None) -> str | None:
    """Normalize a DOI for comparison."""
    if not doi:
        return None

    # Remove URL prefix
    doi = re.sub(r"^https?://doi\.org/", "", doi)

    # Lowercase
    doi = doi.lower()

    # Remove whitespace
    doi = doi.strip()

    return doi


def titles_are_similar(title1: str, title2: str, threshold: float = 0.85) -> bool:
    """Check if two titles are similar enough to be the same paper."""
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)

    if not norm1 or not norm2:
        return False

    # Exact match after normalization
    if norm1 == norm2:
        return True

    # Sequence similarity
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    return similarity >= threshold


def deduplicate_papers(papers: list[RawPaper]) -> list[RawPaper]:
    """Deduplicate papers by DOI and title similarity."""
    if not papers:
        return []

    seen_dois: dict[str, RawPaper] = {}
    seen_titles: list[tuple[str, RawPaper]] = []
    unique_papers: list[RawPaper] = []

    for paper in papers:
        # Check DOI deduplication
        if paper.doi:
            normalized_doi = normalize_doi(paper.doi)
            if normalized_doi and normalized_doi in seen_dois:
                # Merge metadata from duplicate
                existing = seen_dois[normalized_doi]
                _merge_paper_metadata(existing, paper)
                continue
            if normalized_doi:
                seen_dois[normalized_doi] = paper

        # Check title deduplication
        is_duplicate = False
        for seen_title, existing in seen_titles:
            if titles_are_similar(paper.title, seen_title):
                _merge_paper_metadata(existing, paper)
                is_duplicate = True
                break

        if not is_duplicate:
            seen_titles.append((paper.title, paper))
            unique_papers.append(paper)

    return unique_papers


def _merge_paper_metadata(existing: RawPaper, new: RawPaper) -> None:
    """Merge metadata from a new paper into an existing one."""
    # Keep the version with more information
    if not existing.abstract and new.abstract:
        existing.abstract = new.abstract
    if not existing.citation_count and new.citation_count:
        existing.citation_count = new.citation_count
    if not existing.venue and new.venue:
        existing.venue = new.venue
    if not existing.doi and new.doi:
        existing.doi = new.doi

    # Merge authors
    existing_authors = set(existing.authors)
    for author in new.authors:
        if author not in existing_authors:
            existing.authors.append(author)
            existing_authors.add(author)

    # Merge references
    existing_refs = set(existing.references)
    for ref in new.references:
        if ref not in existing_refs:
            existing.references.append(ref)
            existing_refs.add(ref)


def select_papers_for_analysis(
    papers: list[RawPaper],
    max_papers: int = 30,
    min_citations: int = 0,
    require_abstract: bool = False,
) -> list[RawPaper]:
    """Select the best papers for detailed analysis."""
    filtered = papers

    # Filter by minimum citations
    if min_citations > 0:
        filtered = [
            p for p in filtered
            if (p.citation_count or 0) >= min_citations
        ]

    # Filter by abstract availability
    if require_abstract:
        filtered = [p for p in filtered if p.abstract]

    # Sort by relevance score (citations + recency)
    current_year = 2025  # Could be passed as parameter

    def relevance_score(paper: RawPaper) -> float:
        score = 0.0

        # Citation component (0-50 points)
        if paper.citation_count:
            if paper.citation_count > 1000:
                score += 50
            elif paper.citation_count > 100:
                score += 40
            elif paper.citation_count > 10:
                score += 30
            else:
                score += 20

        # Recency component (0-30 points)
        if paper.year:
            years_old = current_year - paper.year
            if years_old <= 1:
                score += 30
            elif years_old <= 3:
                score += 25
            elif years_old <= 5:
                score += 20
            else:
                score += 10

        # Abstract bonus (0-20 points)
        if paper.abstract:
            score += 20

        return score

    filtered.sort(key=relevance_score, reverse=True)

    return filtered[:max_papers]


def group_papers_by_type(papers: list[RawPaper]) -> dict[str, list[RawPaper]]:
    """Group papers by their type."""
    groups: dict[str, list[RawPaper]] = {
        "research": [],
        "review": [],
        "dataset": [],
        "benchmark": [],
        "unknown": [],
    }

    for paper in papers:
        paper_type = paper.paper_type or "unknown"
        if paper_type in groups:
            groups[paper_type].append(paper)
        else:
            groups["unknown"].append(paper)

    return groups


def group_papers_by_year(papers: list[RawPaper]) -> dict[int, list[RawPaper]]:
    """Group papers by publication year."""
    groups: dict[int, list[RawPaper]] = {}

    for paper in papers:
        year = paper.year or 0
        if year not in groups:
            groups[year] = []
        groups[year].append(paper)

    return dict(sorted(groups.items(), reverse=True))


def group_papers_by_venue(papers: list[RawPaper]) -> dict[str, list[RawPaper]]:
    """Group papers by venue."""
    groups: dict[str, list[RawPaper]] = {}

    for paper in papers:
        venue = paper.venue or "Unknown"
        if venue not in groups:
            groups[venue] = []
        groups[venue].append(paper)

    return groups


def calculate_deduplication_stats(
    original: list[RawPaper],
    deduplicated: list[RawPaper],
) -> dict[str, Any]:
    """Calculate deduplication statistics."""
    return {
        "original_count": len(original),
        "deduplicated_count": len(deduplicated),
        "removed_count": len(original) - len(deduplicated),
        "removal_rate": (len(original) - len(deduplicated)) / len(original) if original else 0,
    }
