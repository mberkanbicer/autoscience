"""Paper models."""

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Paper(BaseModel):
    """A scientific paper with metadata."""

    __tablename__ = "papers"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[list] = mapped_column(JSON, default=list)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    venue: Mapped[str | None] = mapped_column(String(500), nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    citation_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    paper_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # research | review | survey | dataset | benchmark
    source_connector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="papers")
    sources = relationship("PaperSource", back_populates="paper", lazy="selectin")
    fulltext = relationship("PaperFulltext", back_populates="paper", uselist=False, lazy="selectin")
    embedding = relationship("PaperEmbedding", back_populates="paper", uselist=False, lazy="selectin")
    analysis = relationship("PaperAnalysis", back_populates="paper", uselist=False, lazy="selectin")

    def __repr__(self) -> str:
        return f"<Paper {self.title[:50]}...>"


class PaperSource(BaseModel):
    """Source metadata for a paper from different connectors."""

    __tablename__ = "paper_sources"

    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    connector: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    paper = relationship("Paper", back_populates="sources")


class PaperFulltext(BaseModel):
    """Full text of a paper when legally available."""

    __tablename__ = "paper_fulltexts"

    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    fulltext: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Relationships
    paper = relationship("Paper", back_populates="fulltext")


class PaperEmbedding(BaseModel):
    """Vector embedding for semantic search."""

    __tablename__ = "paper_embeddings"

    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)  # Will use pgvector in production
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    paper = relationship("Paper", back_populates="embedding")


class PaperAnalysis(BaseModel):
    """Structured analysis of a paper."""

    __tablename__ = "paper_analyses"

    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    problem: Mapped[str | None] = mapped_column(Text, nullable=True)
    method: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_sample: Mapped[str | None] = mapped_column(Text, nullable=True)
    metrics: Mapped[list] = mapped_column(JSON, default=list)
    findings: Mapped[list] = mapped_column(JSON, default=list)
    limitations: Mapped[list] = mapped_column(JSON, default=list)
    future_work: Mapped[list] = mapped_column(JSON, default=list)
    assumptions: Mapped[list] = mapped_column(JSON, default=list)
    relation_to_idea: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_claims: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    paper = relationship("Paper", back_populates="analysis")


class PaperCluster(BaseModel):
    """A cluster of related papers."""

    __tablename__ = "paper_clusters"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cluster_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # topic | method | dataset | claim | application
    paper_ids: Mapped[list] = mapped_column(JSON, default=list)
    representative_paper_id: Mapped[str | None] = mapped_column(nullable=True)

    # Relationships
    labels = relationship("ClusterLabel", back_populates="cluster", lazy="selectin")
    conflicts = relationship("ClusterConflict", back_populates="cluster", lazy="selectin")


class ClusterLabel(BaseModel):
    """Label for a paper cluster."""

    __tablename__ = "cluster_labels"

    cluster_id: Mapped[str] = mapped_column(ForeignKey("paper_clusters.id", ondelete="CASCADE"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    cluster = relationship("PaperCluster", back_populates="labels")


class ClusterConflict(BaseModel):
    """A conflict detected within or between clusters."""

    __tablename__ = "cluster_conflicts"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    cluster_id: Mapped[str | None] = mapped_column(ForeignKey("paper_clusters.id", ondelete="CASCADE"), nullable=True, index=True)
    conflict_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # finding | method | dataset | metric | assumption | scope | theory_practice | recency | replication
    description: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_papers: Mapped[list] = mapped_column(JSON, default=list)
    opposing_papers: Mapped[list] = mapped_column(JSON, default=list)
    research_opportunity: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    cluster = relationship("PaperCluster", back_populates="conflicts")
