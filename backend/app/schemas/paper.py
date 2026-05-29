"""Paper schemas."""

from pydantic import Field

from .base import BaseSchema, TimestampSchema


class PaperCreate(BaseSchema):
    """Schema for creating a paper."""

    title: str = Field(..., min_length=1)
    authors: list[str] = Field(default_factory=list)
    year: int | None = Field(None, ge=1900, le=2100)
    doi: str | None = None
    abstract: str | None = None
    venue: str | None = None
    url: str | None = None
    citation_count: int | None = Field(None, ge=0)
    paper_type: str | None = Field(
        None, pattern="^(research|review|survey|dataset|benchmark)$"
    )
    source_connector: str | None = None
    source_id: str | None = None


class PaperUpdate(BaseSchema):
    """Schema for updating a paper."""

    title: str | None = None
    authors: list[str] | None = None
    year: int | None = Field(None, ge=1900, le=2100)
    doi: str | None = None
    abstract: str | None = None
    venue: str | None = None
    url: str | None = None
    citation_count: int | None = Field(None, ge=0)
    paper_type: str | None = Field(
        None, pattern="^(research|review|survey|dataset|benchmark)$"
    )


class PaperResponse(TimestampSchema):
    """Schema for paper response."""

    project_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    doi: str | None = None
    abstract: str | None = None
    venue: str | None = None
    url: str | None = None
    citation_count: int | None = None
    paper_type: str | None = None
    source_connector: str | None = None
    source_id: str | None = None


class PaperAnalysisResponse(TimestampSchema):
    """Schema for paper analysis response."""

    paper_id: str
    problem: str | None = None
    method: str | None = None
    dataset_sample: str | None = None
    metrics: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    future_work: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    relation_to_idea: str | None = None
    key_claims: list[dict] = Field(default_factory=list)
    confidence: float | None = None


class PaperSearchRequest(BaseSchema):
    """Schema for paper search request."""

    query: str = Field(..., min_length=1)
    sources: list[str] = Field(default_factory=lambda: ["openalex", "semantic_scholar", "arxiv"])
    year_range: tuple[int, int] | None = None
    limit: int = Field(default=50, ge=1, le=200)


class PaperClusterResponse(TimestampSchema):
    """Schema for paper cluster response."""

    project_id: str
    name: str | None = None
    description: str | None = None
    cluster_type: str | None = None
    paper_ids: list[str] = Field(default_factory=list)
    representative_paper_id: str | None = None
    labels: list[dict] = Field(default_factory=list)


class ClusterConflictResponse(TimestampSchema):
    """Schema for cluster conflict response."""

    project_id: str
    cluster_id: str | None = None
    conflict_type: str
    description: str
    supporting_papers: list[str] = Field(default_factory=list)
    opposing_papers: list[str] = Field(default_factory=list)
    research_opportunity: str | None = None
    severity: float | None = None
