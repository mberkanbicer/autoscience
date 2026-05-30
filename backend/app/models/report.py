"""Report and knowledge note models."""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class ResearchReport(BaseModel):
    """A research report generated from a research run."""

    __tablename__ = "research_reports"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    run_id: Mapped[str | None] = mapped_column(ForeignKey("research_runs.id"), nullable=True, index=True)
    idea_id: Mapped[str | None] = mapped_column(ForeignKey("ideas.id"), nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # cycle | idle | validation | summary


class KnowledgeNote(BaseModel):
    """A note in the research wiki/knowledge base."""

    __tablename__ = "knowledge_notes"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    note_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # paper | cluster | conflict | hypothesis | skill | project
    entity_id: Mapped[str | None] = mapped_column(nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)  # pgvector in production
    linked_notes: Mapped[list] = mapped_column(JSON, default=list)


class LiteratureSearch(BaseModel):
    """Record of a literature search."""

    __tablename__ = "literature_searches"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    run_id: Mapped[str | None] = mapped_column(ForeignKey("research_runs.id"), nullable=True, index=True)
    idea_id: Mapped[str | None] = mapped_column(ForeignKey("ideas.id"), nullable=True, index=True)
    total_results: Mapped[int | None] = mapped_column(nullable=True)
    papers_selected: Mapped[int | None] = mapped_column(nullable=True)
    queries_used: Mapped[list] = mapped_column(JSON, default=list)
    connectors_used: Mapped[list] = mapped_column(JSON, default=list)


class SearchQuery(BaseModel):
    """A search query used in literature retrieval."""

    __tablename__ = "search_queries"

    search_id: Mapped[str] = mapped_column(ForeignKey("literature_searches.id"), nullable=False, index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # high_impact | frontier | review | contradiction | dataset | adjacent
    sources: Mapped[list] = mapped_column(JSON, default=list)
    year_range: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result_count: Mapped[int | None] = mapped_column(nullable=True)


class Dataset(BaseModel):
    """A dataset available for analysis."""

    __tablename__ = "datasets"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    format: Mapped[str | None] = mapped_column(String(50), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    row_count: Mapped[int | None] = mapped_column(nullable=True)
    column_count: Mapped[int | None] = mapped_column(nullable=True)
    schema_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AnalysisRun(BaseModel):
    """A data analysis run."""

    __tablename__ = "analysis_runs"

    hypothesis_id: Mapped[str | None] = mapped_column(ForeignKey("hypotheses.id"), nullable=True, index=True)
    dataset_id: Mapped[str | None] = mapped_column(ForeignKey("datasets.id"), nullable=True, index=True)
    script: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class AnalysisArtifact(BaseModel):
    """An artifact produced by an analysis run."""

    __tablename__ = "analysis_artifacts"

    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id"), nullable=False, index=True)
    artifact_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # figure | table | json | csv | script
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
