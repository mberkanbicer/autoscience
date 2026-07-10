"""Serialize connector paper objects for Redis caching."""

from __future__ import annotations

from typing import Any

from .base import RawPaper, SearchQuery, SearchResult


def paper_to_dict(paper: RawPaper) -> dict[str, Any]:
    return {
        "source": paper.source,
        "source_id": paper.source_id,
        "title": paper.title,
        "authors": paper.authors,
        "year": paper.year,
        "doi": paper.doi,
        "abstract": paper.abstract,
        "venue": paper.venue,
        "url": paper.url,
        "citation_count": paper.citation_count,
        "paper_type": paper.paper_type,
        "references": paper.references,
        "raw_metadata": paper.raw_metadata,
    }


def paper_from_dict(data: dict[str, Any]) -> RawPaper:
    return RawPaper(
        source=data["source"],
        source_id=data["source_id"],
        title=data["title"],
        authors=data.get("authors") or [],
        year=data.get("year"),
        doi=data.get("doi"),
        abstract=data.get("abstract"),
        venue=data.get("venue"),
        url=data.get("url"),
        citation_count=data.get("citation_count"),
        paper_type=data.get("paper_type"),
        references=data.get("references") or [],
        raw_metadata=data.get("raw_metadata") or {},
    )


def search_result_to_dict(result: SearchResult) -> dict[str, Any]:
    return {
        "source": result.source,
        "query": {
            "text": result.query.text,
            "year_from": result.query.year_from,
            "year_to": result.query.year_to,
            "limit": result.query.limit,
            "paper_type": result.query.paper_type,
            "sort_by": result.query.sort_by,
        },
        "papers": [paper_to_dict(p) for p in result.papers],
        "total_results": result.total_results,
        "has_more": result.has_more,
        "next_offset": result.next_offset,
    }


def search_result_from_dict(data: dict[str, Any]) -> SearchResult:
    query_data = data["query"]
    query = SearchQuery(
        text=query_data["text"],
        year_from=query_data.get("year_from"),
        year_to=query_data.get("year_to"),
        limit=query_data.get("limit", 20),
        paper_type=query_data.get("paper_type"),
        sort_by=query_data.get("sort_by", "relevance"),
    )
    return SearchResult(
        source=data["source"],
        query=query,
        papers=[paper_from_dict(p) for p in data.get("papers", [])],
        total_results=data.get("total_results", 0),
        has_more=data.get("has_more", False),
        next_offset=data.get("next_offset"),
    )
