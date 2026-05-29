# Master Implementation Plan: Background Scientific Cognition System

## Decisions

| Decision | Choice |
|---|---|
| Team | Solo developer |
| Timeline | Open-ended (correctness over speed) |
| LLM Provider | Multi-provider (OpenAI, Anthropic, local models) |
| Frontend | Full web dashboard (Next.js + React + Tailwind) |
| Backend | Python + FastAPI + PostgreSQL + Redis |
| Agent Runtime | LangGraph-style durable workflows + provider abstraction |

---

## Project Directory Structure

```
autoscience/
├── docs/
│   ├── architecture.md
│   ├── data-model.md
│   ├── api-design.md
│   ├── safety-policy.md
│   ├── development-standards.md
│   └── roadmap.md
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry
│   │   ├── config.py                  # Settings / env
│   │   ├── dependencies.py            # DI providers
│   │   ├── models/                    # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── project.py
│   │   │   ├── idea.py
│   │   │   ├── research_run.py
│   │   │   ├── paper.py
│   │   │   ├── cluster.py
│   │   │   ├── conflict.py
│   │   │   ├── research_question.py
│   │   │   ├── hypothesis.py
│   │   │   ├── validation_plan.py
│   │   │   ├── skill.py
│   │   │   ├── report.py
│   │   │   ├── audit.py
│   │   │   ├── idle_cycle.py
│   │   │   ├── dataset.py
│   │   │   └── knowledge_note.py
│   │   ├── schemas/                   # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── project.py
│   │   │   ├── idea.py
│   │   │   ├── research_run.py
│   │   │   ├── paper.py
│   │   │   ├── cluster.py
│   │   │   ├── conflict.py
│   │   │   ├── research_question.py
│   │   │   ├── hypothesis.py
│   │   │   ├── validation_plan.py
│   │   │   ├── skill.py
│   │   │   ├── report.py
│   │   │   ├── audit.py
│   │   │   ├── idle_cycle.py
│   │   │   ├── dataset.py
│   │   │   └── knowledge_note.py
│   │   ├── api/                       # API routes
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── projects.py
│   │   │   ├── ideas.py
│   │   │   ├── research_runs.py
│   │   │   ├── papers.py
│   │   │   ├── clusters.py
│   │   │   ├── conflicts.py
│   │   │   ├── research_questions.py
│   │   │   ├── hypotheses.py
│   │   │   ├── validation_plans.py
│   │   │   ├── skills.py
│   │   │   ├── reports.py
│   │   │   ├── idle.py
│   │   │   ├── datasets.py
│   │   │   ├── knowledge.py
│   │   │   ├── approval.py
│   │   │   └── audit.py
│   │   ├── services/                  # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── project_service.py
│   │   │   ├── idea_service.py
│   │   │   ├── research_run_service.py
│   │   │   ├── paper_service.py
│   │   │   ├── cluster_service.py
│   │   │   ├── conflict_service.py
│   │   │   ├── research_question_service.py
│   │   │   ├── hypothesis_service.py
│   │   │   ├── validation_service.py
│   │   │   ├── scoring_service.py
│   │   │   ├── skill_service.py
│   │   │   ├── report_service.py
│   │   │   ├── idle_service.py
│   │   │   ├── knowledge_service.py
│   │   │   └── audit_service.py
│   │   ├── agents/                    # Agent definitions
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Base agent class
│   │   │   ├── orchestrator.py
│   │   │   ├── user_intent.py
│   │   │   ├── idle_cognition.py
│   │   │   ├── literature.py
│   │   │   ├── paper_analyst.py
│   │   │   ├── cluster_agent.py
│   │   │   ├── conflict_agent.py
│   │   │   ├── research_question.py
│   │   │   ├── hypothesis_agent.py
│   │   │   ├── validation_planner.py
│   │   │   ├── data_analyst.py
│   │   │   ├── skeptic.py
│   │   │   ├── decision.py
│   │   │   ├── skill_curator.py
│   │   │   └── archivist.py
│   │   ├── llm/                       # LLM provider abstraction
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Base LLM provider
│   │   │   ├── openai_provider.py
│   │   │   ├── anthropic_provider.py
│   │   │   ├── local_provider.py
│   │   │   ├── router.py             # Provider router/selector
│   │   │   └── prompts/              # Prompt templates
│   │   │       ├── paper_analysis.py
│   │   │       ├── question_generation.py
│   │   │       ├── hypothesis_generation.py
│   │   │       ├── scoring.py
│   │   │       ├── skill_creation.py
│   │   │       └── conflict_detection.py
│   │   ├── connectors/               # Academic source connectors
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── openalex.py
│   │   │   ├── semantic_scholar.py
│   │   │   ├── crossref.py
│   │   │   ├── arxiv.py
│   │   │   ├── pubmed.py
│   │   │   ├── doaj.py
│   │   │   ├── core.py
│   │   │   └── unpaywall.py
│   │   ├── engine/                   # Core engines
│   │   │   ├── __init__.py
│   │   │   ├── literature_engine.py
│   │   │   ├── clustering_engine.py
│   │   │   ├── conflict_engine.py
│   │   │   ├── question_engine.py
│   │   │   ├── hypothesis_engine.py
│   │   │   ├── validation_engine.py
│   │   │   ├── scoring_engine.py
│   │   │   ├── idle_engine.py
│   │   │   ├── skill_engine.py
│   │   │   └── knowledge_engine.py
│   │   ├── workflows/                 # LangGraph-style workflows
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── user_research.py
│   │   │   ├── idle_citation_conflict.py
│   │   │   ├── idle_frontier_scan.py
│   │   │   ├── idle_revisit_rejected.py
│   │   │   ├── idle_cross_domain.py
│   │   │   └── validation_workflow.py
│   │   ├── sandbox/                   # Data analysis sandbox
│   │   │   ├── __init__.py
│   │   │   ├── executor.py
│   │   │   ├── docker_runner.py
│   │   │   └── artifacts.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── embeddings.py
│   │       ├── text.py
│   │       ├── dedup.py
│   │       └── rate_limiter.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_models/
│   │   ├── test_services/
│   │   ├── test_connectors/
│   │   ├── test_engines/
│   │   ├── test_agents/
│   │   └── test_api/
│   └── scripts/
│       ├── seed_data.py
│       └── run_idle.py
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── projects/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx
│   │   │   │       ├── ideas/
│   │   │   │       ├── runs/
│   │   │   │       ├── papers/
│   │   │   │       ├── clusters/
│   │   │   │       ├── questions/
│   │   │   │       ├── hypotheses/
│   │   │   │       ├── skills/
│   │   │   │       ├── reports/
│   │   │   │       ├── wiki/
│   │   │   │       ├── settings/
│   │   │   │       └── approval/
│   │   │   └── api/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   └── Footer.tsx
│   │   │   ├── projects/
│   │   │   ├── ideas/
│   │   │   ├── papers/
│   │   │   ├── clusters/
│   │   │   ├── skills/
│   │   │   ├── charts/
│   │   │   └── common/
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── types.ts
│   │   └── styles/
│   │       └── globals.css
│   └── public/
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── Dockerfile.sandbox
│   └── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── complete_background_scientific_cognition_system_build_blueprint.md
└── reference_projects_and_full_system_build_plan.md
```

---

## Phase 1: Repository and Product Specification

**Goal**: Create the project foundation with documentation.

### Tasks

1. Initialize git repository
2. Create directory structure
3. Create `.gitignore`
4. Create `.env.example`
5. Create `README.md` with project overview
6. Create `docs/architecture.md`
7. Create `docs/data-model.md`
8. Create `docs/api-design.md`
9. Create `docs/safety-policy.md`
10. Create `docs/development-standards.md`
11. Create `docs/roadmap.md`

### Acceptance Criteria

- [ ] Repository initialized with git
- [ ] All directories created
- [ ] Documentation covers system vision, architecture, data model, API, safety, and standards
- [ ] A new contributor can understand the project from docs alone

---

## Phase 2: Backend Foundation

**Goal**: Build the backend skeleton with database, API, and tests.

### Tasks

1. Create `backend/pyproject.toml` with dependencies:
   - fastapi, uvicorn, sqlalchemy, alembic, pydantic, asyncpg, redis, celery/dramatiq, httpx, pytest
2. Create `backend/app/config.py` — environment-based settings
3. Create `backend/app/main.py` — FastAPI app with CORS, health check
4. Create `backend/app/models/base.py` — SQLAlchemy base with UUID PKs, timestamps
5. Create core models:
   - Project, Idea, ResearchRun, Paper, Skill, AuditLog
6. Create Alembic configuration and initial migration
7. Create `backend/app/schemas/` for all core models
8. Create `backend/app/api/router.py` — API router aggregation
9. Create basic CRUD endpoints for Project
10. Create `backend/tests/conftest.py` with test database setup
11. Create tests for Project CRUD
12. Create `docker/docker-compose.yml` with PostgreSQL + Redis

### Core Model: Project

```python
class Project(Base):
    __tablename__ = "projects"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255))
    domain: Mapped[str] = mapped_column(String(500))
    subject_scope: Mapped[list] = mapped_column(JSON, default=list)
    out_of_scope: Mapped[list] = mapped_column(JSON, default=list)
    default_flexibility: Mapped[float] = mapped_column(Float, default=0.6)
    idle_research_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    idle_trigger_minutes: Mapped[int] = mapped_column(Integer, default=120)
    max_idle_cycles_per_day: Mapped[int] = mapped_column(Integer, default=3)
    max_sources_per_cycle: Mapped[int] = mapped_column(Integer, default=50)
    approval_required_for_external_actions: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=func.now())
```

### Acceptance Criteria

- [ ] Backend starts locally with `uvicorn app.main:app`
- [ ] PostgreSQL connects via SQLAlchemy
- [ ] Alembic migrations run successfully
- [ ] CRUD endpoints return correct responses
- [ ] Tests pass
- [ ] Docker Compose brings up PostgreSQL + Redis

---

## Phase 3: Complete Data Model

**Goal**: Implement all database tables.

### Tasks

1. Create all model files under `backend/app/models/`:

```
project.py       → Project, ProjectSettings
idea.py          → Idea, IdeaVersion, IdeaScore, IdeaClassification, IdeaDecision
research_run.py  → ResearchRun, ResearchRunEvent
paper.py         → Paper, PaperSource, PaperFulltext, PaperEmbedding, PaperAnalysis
cluster.py       → PaperCluster, ClusterLabel
conflict.py      → ClusterConflict
research_question.py → ResearchQuestion
hypothesis.py    → Hypothesis
validation_plan.py → ValidationPlan, Dataset, AnalysisRun, AnalysisArtifact
skill.py         → Skill, SkillVersion, SkillUsage, SkillEvaluation
report.py        → ResearchReport
audit.py         → AuditLog, ToolCall, ApprovalRequest, SystemEvent
idle_cycle.py    → IdleCycle
knowledge_note.py → KnowledgeNote
literature_search.py → LiteratureSearch, SearchQuery
```

2. Define all relationships and foreign keys
3. Create composite indexes for common queries
4. Create database views for idea ledger, skill dashboard
5. Generate and run Alembic migration
6. Write model tests for all relationships

### Acceptance Criteria

- [ ] All 30+ tables created
- [ ] All relationships defined correctly
- [ ] Migration applies cleanly
- [ ] Model tests verify relationships

---

## Phase 4: Research State and Audit Log

**Goal**: Make every workflow stateful and auditable.

### Tasks

1. Create `ResearchState` schema — the state object passed through workflows
2. Create `ResearchRunEvent` model with event types:
   - `run_started`, `agent_invoked`, `tool_called`, `decision_made`,
     `idea_scored`, `conflict_detected`, `question_generated`,
     `hypothesis_formed`, `skill_created`, `run_paused`,
     `run_resumed`, `run_completed`, `run_failed`
3. Create `AuditLog` model with fields:
   - `run_id`, `event_type`, `actor`, `action`, `details`, `timestamp`
4. Create `ToolCall` model:
   - `run_id`, `agent_role`, `tool_name`, `input`, `output`, `duration_ms`, `success`
5. Create `audit_service.py` — functions to log events
6. Create snapshot export — JSON dump of full run state
7. Add run timeline API endpoint

### ResearchState Schema

```python
class ResearchState(BaseModel):
    run_id: UUID
    project_id: UUID
    idea_id: UUID
    run_type: str  # user_directed | flexible_user | idle_autonomous | validation
    current_phase: str
    original_idea: str
    current_idea: str
    flexibility: float
    budget: RunBudget
    papers: list[PaperSummary]
    clusters: list[ClusterSummary]
    conflicts: list[ConflictSummary]
    questions: list[QuestionSummary]
    hypotheses: list[HypothesisSummary]
    scores: list[IdeaScoreSummary]
    skills_used: list[UUID]
    skills_created: list[UUID]
    events: list[RunEvent]
```

### Acceptance Criteria

- [ ] Every state transition logged
- [ ] Every tool call logged
- [ ] Every decision logged
- [ ] Failed runs preserve logs
- [ ] Snapshot export works

---

## Phase 5: LLM Provider Abstraction

**Goal**: Build a multi-provider LLM layer.

### Tasks

1. Create `backend/app/llm/base.py` — abstract LLM provider:

```python
class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, messages: list[Message], model: str, **kwargs) -> str: ...

    @abstractmethod
    async def complete_structured(self, messages: list[Message], schema: dict, model: str) -> dict: ...

    @abstractmethod
    def count_tokens(self, text: str) -> int: ...
```

2. Create `backend/app/llm/openai_provider.py`:
   - Uses `openai` async client
   - Supports GPT-4o, GPT-4o-mini, o3-mini
   - Structured output via response_format

3. Create `backend/app/llm/anthropic_provider.py`:
   - Uses `anthropic` async client
   - Supports Claude Sonnet 4, Claude Haiku
   - Structured output via tool use

4. Create `backend/app/llm/local_provider.py`:
   - Uses `httpx` to call Ollama/vLLM endpoints
   - Configurable base URL and model name

5. Create `backend/app/llm/router.py`:
   - Provider selection based on config
   - Fallback chain (primary → secondary → local)
   - Cost tracking per call
   - Rate limiting per provider

6. Create `backend/app/llm/prompts/`:
   - All prompt templates as Python functions
   - Version-controlled prompts
   - Token-efficient templates

7. Create provider tests

### Acceptance Criteria

- [ ] All three providers work
- [ ] Provider switching is seamless
- [ ] Fallback chain works
- [ ] Cost tracking per call
- [ ] Prompt templates are versioned

---

## Phase 6: Academic Source Connectors

**Goal**: Connect to scholarly metadata sources.

### Tasks

1. Create `backend/app/connectors/base.py`:

```python
class AcademicConnector(ABC):
    @abstractmethod
    async def search(self, query: SearchQuery, limit: int) -> list[RawPaper]: ...

    @abstractmethod
    async def get_paper(self, identifier: str) -> RawPaper | None: ...

    @abstractmethod
    async def get_citations(self, paper_id: str, limit: int) -> list[RawPaper]: ...

    @abstractmethod
    async def get_references(self, paper_id: str, limit: int) -> list[RawPaper]: ...
```

2. Implement connectors:
   - `openalex.py` — OpenAlex API (free, no key required for basic use)
   - `semantic_scholar.py` — Semantic Scholar API (free tier available)
   - `crossref.py` — Crossref API (free)
   - `arxiv.py` — arXiv API (free)
   - `pubmed.py` — PubMed/NCBI E-utilities (free)
   - `doaj.py` — DOAJ API (free)
   - `core.py` — CORE API (free with API key)
   - `unpaywall.py` — Unpaywall API (free with email)

3. Create paper metadata normalizer:
   - Normalize title, authors, year, DOI, abstract, venue, citations
   - Deduplicate across sources by DOI, then by title similarity
   - Store provenance (which source provided which fields)

4. Create rate limiter for each connector
5. Create retry logic with exponential backoff
6. Create connector tests using mock responses

### Acceptance Criteria

- [ ] All 8 connectors implemented
- [ ] Metadata normalized consistently
- [ ] Deduplication works across sources
- [ ] Rate limits respected
- [ ] Retry logic handles transient failures
- [ ] Tests pass with mocked responses

---

## Phase 7: Keyword Expansion and Search Planning

**Goal**: Turn ideas into high-quality academic search strategies.

### Tasks

1. Create `backend/app/engine/literature_engine.py`:

```python
class LiteratureEngine:
    async def plan_search(self, idea: str, project: Project) -> SearchPlan: ...

class SearchPlan:
    core_concepts: list[str]
    synonyms: list[str]
    method_terms: list[str]
    application_terms: list[str]
    metric_terms: list[str]
    adjacent_field_terms: list[str]
    negative_terms: list[str]
    queries: list[SearchQuery]

class SearchQuery:
    text: str
    query_type: str  # high_impact | frontier | review | contradiction | dataset | adjacent
    sources: list[str]
    year_range: tuple[int, int]
    limit: int
```

2. Create keyword expansion logic:
   - Extract core concepts from idea text
   - Generate synonyms via LLM
   - Generate method-specific terms
   - Generate application-domain terms
   - Generate metric terms
   - Generate adjacent-field terms (for cross-domain discovery)
   - Generate negative terms (to exclude irrelevant results)

3. Create search plan builder:
   - High-impact query (top-cited, last 5 years)
   - Frontier query (recent 6-12 months)
   - Review/survey query
   - Contradiction query (search for opposing findings)
   - Dataset/benchmark query
   - Adjacent-field query

4. Store search plan with rationale for each query

### Acceptance Criteria

- [ ] Every idea produces a multi-query search plan
- [ ] Search terms include adjacent terminology
- [ ] System can explain why each query exists
- [ ] Plans stored in database

---

## Phase 8: Literature Retrieval and Ranking

**Goal**: Retrieve and rank relevant papers.

### Tasks

1. Create retrieval pipeline in `literature_engine.py`:
   - Execute all queries from search plan across connectors
   - Merge results
   - Deduplicate
   - Normalize metadata

2. Create paper ranking function:

```python
def rank_papers(papers: list[Paper], idea: str) -> list[RankedPaper]:
    # Score by: relevance, citations, recency, venue quality,
    # semantic similarity, review/survey status, limitation disclosure,
    # prior-art proximity, assumption-challenging potential
```

3. Create paper selection:
   - Select top 20 high-impact papers
   - Select top 20 frontier papers
   - Select 5-10 review papers
   - Select contradictory papers
   - Select dataset/benchmark papers
   - Store selection reasons

4. Create retrieval tests

### Acceptance Criteria

- [ ] System retrieves papers from all initial sources
- [ ] Papers ranked by multiple criteria
- [ ] Selection reasons logged
- [ ] Deduplication works

---

## Phase 9: Paper Analysis Engine

**Goal**: Extract structured information from papers.

### Tasks

1. Create paper analysis prompts in `llm/prompts/paper_analysis.py`
2. Create `PaperAnalysis` extraction:

```python
class PaperExtraction:
    problem: str
    method: str
    dataset_or_sample: str
    metrics: list[str]
    findings: list[str]
    limitations: list[str]
    future_work: list[str]
    assumptions: list[str]
    relation_to_idea: str
    key_claims: list[Claim]
    confidence: float

class Claim:
    text: str
    type: str  # finding | method | limitation | assumption
    evidence: str
    confidence: float
```

3. Analyze abstracts first (fast pass)
4. Retrieve full text when legally available
5. Deep analysis on selected papers
6. Store structured extraction in `PaperAnalysis` table
7. Create evidence table linking claims to papers

### Acceptance Criteria

- [ ] Each selected paper has structured analysis
- [ ] Extracted facts separated from interpretation
- [ ] Claims linked to source papers
- [ ] Full text used when available

---

## Phase 10: Clustering and Literature Map

**Goal**: Group papers into meaningful themes.

### Tasks

1. Create `backend/app/engine/clustering_engine.py`
2. Create embedding generation for papers:
   - Use sentence-transformers or LLM embeddings
   - Embed paper title + abstract + key findings
3. Create clustering:
   - Semantic similarity clustering (primary)
   - Method-based clustering
   - Dataset-based clustering
   - Claim/finding-based clustering
4. Create cluster labeling:
   - LLM-generated cluster labels
   - Representative paper selection per cluster
   - Cluster summary generation
5. Create cluster relationship detection:
   - Inter-cluster connections
   - Method overlap
   - Dataset sharing
6. Store clusters in `PaperCluster` and `ClusterLabel` tables

### Acceptance Criteria

- [ ] Papers grouped into interpretable clusters
- [ ] Each cluster has clear theme and label
- [ ] Representative papers identified
- [ ] Cluster summaries generated

---

## Phase 11: Conflict and Gap Detection

**Goal**: Find useful research tensions.

### Tasks

1. Create `backend/app/engine/conflict_engine.py`
2. Create conflict detection logic:
   - Compare findings inside clusters
   - Compare methods inside clusters
   - Compare datasets
   - Compare metrics
   - Compare assumptions
   - Detect repeated limitations
   - Detect missing baselines
   - Detect weak validation patterns
   - Detect recency conflicts (new vs old consensus)
3. Create conflict classification:

```python
class Conflict:
    conflict_id: UUID
    cluster_id: UUID
    type: str  # finding | method | dataset | metric | assumption |
               # scope | theory_practice | recency | replication
    description: str
    supporting_papers: list[UUID]
    opposing_papers: list[UUID]
    research_opportunity: str
    severity: float  # 0-1
```

4. Create gap detection:
   - Repeated limitations across papers
   - Missing validation
   - Missing baselines
   - Underexplored conditions
5. Store conflicts in `ClusterConflict` table

### Acceptance Criteria

- [ ] All 9 conflict types detected
- [ ] Each conflict cites supporting papers
- [ ] Each gap includes research opportunity
- [ ] Conflicts categorized and severity-scored

---

## Phase 12: Research Question Generator

**Goal**: Derive research questions from conflicts and gaps.

### Tasks

1. Create `backend/app/engine/question_engine.py`
2. Create question generation from conflicts:

```python
class QuestionGenerator:
    async def generate_from_conflicts(
        self, conflicts: list[Conflict], papers: list[Paper]
    ) -> list[ResearchQuestion]: ...

    async def generate_from_gaps(
        self, gaps: list[Gap], papers: list[Paper]
    ) -> list[ResearchQuestion]: ...
```

3. Create question templates:
   - "Why do papers using [method A] find [result X] while papers using [method B] find [result Y]?"
   - "Does [method] still work under [new condition]?"
   - "Is the improvement caused by [mechanism] or by [dataset artifact]?"
   - "Can [method from adjacent field] solve [repeated limitation]?"
   - "What happens if [frontier method] is combined with [unresolved limitation]?"

4. Create question deduplication
5. Create question ranking (by novelty, feasibility, evidence support)
6. Store questions in `ResearchQuestion` table
7. Store rejected questions with reasons

### Acceptance Criteria

- [ ] Every question has evidence trail
- [ ] Weak questions rejected with reasons
- [ ] Top questions suitable for hypothesis generation
- [ ] Questions linked to source conflicts

---

## Phase 13: Hypothesis Generator

**Goal**: Convert research questions into testable hypotheses.

### Tasks

1. Create `backend/app/engine/hypothesis_engine.py`
2. Create hypothesis generation:

```python
class Hypothesis:
    hypothesis_id: UUID
    question_id: UUID
    statement: str
    independent_variable: str
    dependent_variable: str
    context: str
    expected_direction: str
    baseline: str
    metric: str
    dataset_requirement: str
    failure_condition: str
    confidence: float
```

3. Create hypothesis refinement loop
4. Create hypothesis versioning
5. Store in `Hypothesis` table

### Acceptance Criteria

- [ ] Every hypothesis is testable
- [ ] Every hypothesis has failure conditions
- [ ] Hypotheses are not vague restatements of ideas
- [ ] Version history maintained

---

## Phase 14: Validation Planner

**Goal**: Design how to test hypotheses.

### Tasks

1. Create `backend/app/engine/validation_engine.py`
2. Create validation plan generation:

```python
class ValidationPlan:
    plan_id: UUID
    hypothesis_id: UUID
    dataset_candidates: list[DatasetCandidate]
    benchmark_candidates: list[str]
    baselines: list[str]
    metrics: list[str]
    experimental_design: str
    statistical_tests: list[str]
    simulation_option: str | None
    expected_artifacts: list[str]
    difficulty_estimate: float
    cost_estimate: float
    feasibility_score: float
```

3. Search for datasets and benchmarks
4. Identify baselines
5. Define experimental design
6. Estimate cost and difficulty
7. Update idea score based on validation feasibility

### Acceptance Criteria

- [ ] Every promising hypothesis has validation plan
- [ ] Plan includes data, baseline, metric, failure condition
- [ ] If validation not feasible, idea downgraded
- [ ] Cost and difficulty estimated

---

## Phase 15: Idea Scoring Engine

**Goal**: Score every idea and classify it honestly.

### Tasks

1. Create `backend/app/engine/scoring_engine.py`
2. Implement scoring criteria (0-10 each):

```python
class IdeaScore:
    novelty: float
    feasibility: float
    importance: float
    evidence_support: float
    validation_clarity: float
    differentiation: float
    data_availability: float
    skill_leverage: float
    user_alignment: float
    prior_art_risk: float    # negative weight
    safety_risk: float       # negative weight
    cost_risk: float         # negative weight

    def overall_value(self) -> float:
        return (
            0.18 * self.novelty
            + 0.14 * self.feasibility
            + 0.14 * self.importance
            + 0.12 * self.evidence_support
            + 0.14 * self.validation_clarity
            + 0.12 * self.differentiation
            + 0.08 * self.data_availability
            + 0.05 * self.skill_leverage
            + 0.03 * self.user_alignment
            - 0.15 * self.prior_art_risk
            - 0.05 * self.safety_risk
            - 0.03 * self.cost_risk
        )
```

3. Create classification:

```python
def classify(score: float) -> str:
    if score >= 8.0: return "high_value"
    if score >= 6.5: return "promising"
    if score >= 5.0: return "incremental"
    if score >= 3.5: return "weak"
    return "reject"
```

4. Create explanation generator (LLM-based justification)
5. Store scores in `IdeaScore` and `IdeaClassification` tables

### Acceptance Criteria

- [ ] Every idea gets score and classification
- [ ] Scores justified with explanations
- [ ] Rejected ideas stored, not deleted
- [ ] Formula matches blueprint specification

---

## Phase 16: Idea Ledger

**Goal**: Create permanent memory of all ideas.

### Tasks

1. Create `backend/app/services/idea_service.py`
2. Implement idea lifecycle:
   - Create idea (from user prompt or idle generation)
   - Track versions
   - Track score history
   - Track classification changes
   - Track decisions (continue, revise, pivot, archive, reject, promote)
3. Create idea ledger API endpoints:
   - List all ideas with filters
   - Get idea detail with full history
   - Get idea versions
   - Get idea scores
   - Get linked papers, clusters, conflicts, questions, hypotheses
4. Create idea revival logic:
   - When new literature appears, check if rejected ideas deserve reassessment
5. Create idea search (semantic + keyword)

### Acceptance Criteria

- [ ] User can see all ideas
- [ ] User can see why each idea was accepted/rejected
- [ ] System can reuse old rejected ideas if new evidence appears
- [ ] Full version history maintained

---

## Phase 17: Skill Memory System

**Goal**: Make the system learn reusable research methods.

### Tasks

1. Create `backend/app/services/skill_service.py`
2. Implement skill schema:

```python
class Skill:
    skill_id: UUID
    name: str
    skill_type: str  # planning | functional | atomic | domain | evaluation | data | reporting | safety
    purpose: str
    trigger_conditions: list[str]
    inputs: list[str]
    procedure: list[str]
    outputs: list[str]
    status: str  # candidate | tested | active | revised | deprecated | retired
    version: str
    performance: SkillPerformance

class SkillPerformance:
    times_used: int
    successful_uses: int
    average_score_improvement: float | None
    failure_cases: list[str]
    domains_where_it_works: list[str]
    domains_where_it_fails: list[str]
```

3. Create skill creation triggers:
   - Workflow succeeds repeatedly
   - Failure reveals reusable prevention rule
   - Search strategy works well
   - Scoring method improves classification
   - User preference repeats
   - Data-analysis script is reusable

4. Create skill retrieval:
   - Match skills to current context
   - Rank by relevance and performance
   - Load skill into agent context

5. Create skill lifecycle management:
   - Candidate → Tested → Active → Revised → Deprecated → Retired
   - Version tracking
   - Performance monitoring

6. Create skill browser API endpoints

### Acceptance Criteria

- [ ] System creates candidate skills
- [ ] Retrieves relevant skills for new runs
- [ ] Tracks whether skills help
- [ ] Weak skills revised or retired
- [ ] Full lifecycle tracked

---

## Phase 18: Idle Cognition Engine

**Goal**: Allow autonomous background research.

### Tasks

1. Create `backend/app/engine/idle_engine.py`
2. Implement idle trigger:

```python
class IdleTrigger:
    def should_start(self, project: Project, active_runs: int, user_inactive_minutes: int) -> bool:
        return (
            project.idle_research_enabled
            and active_runs == 0
            and user_inactive_minutes >= project.idle_trigger_minutes
            and self.daily_budget_remaining(project)
        )
```

3. Implement idle mode selector (weighted random):
   - 35% Literature frontier scan
   - 25% Citation-conflict question generation
   - 15% Revisit rejected ideas
   - 10% Cross-domain collision
   - 10% Skill improvement
   - 5% Dataset discovery

4. Implement each idle mode as a workflow
5. Implement idle budget manager
6. Create idle cycle logging
7. Create idle run reports
8. Create scheduler (APScheduler or Celery Beat)

### Acceptance Criteria

- [ ] System starts idle cycles only when allowed
- [ ] Idle cycles stay inside project scope
- [ ] Idle cycles respect budgets
- [ ] Every idle idea scored and logged
- [ ] Scheduler runs correctly

---

## Phase 19: Agent Definitions

**Goal**: Formalize all 15 specialized agents.

### Tasks

1. Create `backend/app/agents/base.py`:

```python
class ResearchAgent:
    role: str
    description: str
    tools: list[str]
    provider_preference: str | None
    system_prompt: str

    async def run(self, state: ResearchState, input: AgentInput) -> AgentOutput: ...
```

2. Implement all 15 agents:
   - OrchestratorAgent — controls run flow
   - UserIntentAgent — interprets prompts
   - IdleCognitionAgent — runs idle cycles
   - LiteratureAgent — searches sources
   - PaperAnalystAgent — extracts structured info
   - ClusterAgent — groups papers
   - ConflictAgent — finds tensions
   - ResearchQuestionAgent — generates questions
   - HypothesisAgent — forms hypotheses
   - ValidationPlannerAgent — designs tests
   - DataAnalystAgent — runs analysis
   - SkepticAgent — challenges everything
   - DecisionAgent — chooses next action
   - SkillCuratorAgent — creates/updates skills
   - ArchivistAgent — documents everything

3. Define agent permissions (which tools each can use)
4. Define handoff rules
5. Create agent tests

### Acceptance Criteria

- [ ] All 15 agents implemented
- [ ] Each agent has clear responsibilities
- [ ] Tool permissions defined
- [ ] Handoff rules implemented
- [ ] Tests pass

---

## Phase 20: Workflow Engine

**Goal**: Create durable, resumable research workflows.

### Tasks

1. Create `backend/app/workflows/base.py`:

```python
class ResearchWorkflow:
    workflow_id: str
    steps: list[WorkflowStep]

    async def run(self, state: ResearchState) -> ResearchState: ...
    async def pause(self, state: ResearchState) -> None: ...
    async def resume(self, state: ResearchState) -> ResearchState: ...
```

2. Create workflows:
   - `user_research.py` — full user-directed research cycle
   - `idle_citation_conflict.py` — citation-conflict idle mode
   - `idle_frontier_scan.py` — frontier scan idle mode
   - `idle_revisit_rejected.py` — rejected idea revival
   - `idle_cross_domain.py` — cross-domain collision
   - `validation_workflow.py` — hypothesis validation

3. Create state checkpointing
4. Create pause/resume with approval interrupts
5. Create failure recovery
6. Create workflow tracing

### User Research Workflow

```
1. Receive user idea
2. Interpret intent (strict/flexible)
3. Plan search
4. Retrieve literature
5. Analyze papers
6. Cluster papers
7. Detect conflicts
8. Generate questions
9. Form hypotheses
10. Design validation
11. Score idea
12. Classify idea
13. Create/update skills
14. Generate report
15. Update wiki
16. Log audit trail
```

### Acceptance Criteria

- [ ] All workflows implemented
- [ ] State persists across long runs
- [ ] Runs can pause for approval and resume
- [ ] Failure recovery works
- [ ] Handoffs logged

---

## Phase 21: Data Analysis Sandbox

**Goal**: Safe, reproducible data analysis.

### Tasks

1. Create `backend/app/sandbox/docker_runner.py`:
   - Docker container management
   - Restricted filesystem access
   - Restricted network access by policy
   - Resource limits (CPU, memory, time)

2. Create `backend/app/sandbox/executor.py`:
   - Script generation from analysis plan
   - Script execution in sandbox
   - Output capture
   - Error handling

3. Create `backend/app/sandbox/artifacts.py`:
   - Figure storage
   - Table storage
   - Script storage
   - Result linking to hypotheses

4. Create dataset upload and metadata
5. Create Dockerfile.sandbox with analysis dependencies

### Acceptance Criteria

- [ ] Code never runs on host
- [ ] All artifacts saved
- [ ] Simulated data clearly labeled
- [ ] Results reproducible

---

## Phase 22: Knowledge Base and Research Wiki

**Goal**: Create readable persistent knowledge.

### Tasks

1. Create `backend/app/engine/knowledge_engine.py`
2. Create note generation:
   - Paper notes
   - Cluster notes
   - Conflict notes
   - Hypothesis notes
   - Skill notes
   - Project summaries
3. Create note linking
4. Create semantic search over notes
5. Create wiki generation from structured data
6. Create export (Markdown, HTML)

### Wiki Sections

```
- Project overview
- Active research themes
- Literature maps
- Important papers
- Open conflicts
- Research questions
- Active hypotheses
- Rejected ideas
- Validated ideas
- Skills
- Datasets
- Reports
- Decision history
```

### Acceptance Criteria

- [ ] System creates readable project knowledge base
- [ ] Notes linked to structured data
- [ ] User can search past research
- [ ] Wiki generated from data, not manually maintained

---

## Phase 23: Reporting System

**Goal**: Generate complete research outputs.

### Tasks

1. Create `backend/app/services/report_service.py`
2. Create report sections:
   - Executive summary
   - Original idea
   - Revised idea
   - Flexibility level
   - Sources searched
   - Search queries
   - Paper table
   - Clusters
   - Conflicts
   - Research questions
   - Hypotheses
   - Validation plan
   - Scores
   - Classification
   - Decision
   - Skills used
   - Skills created
   - Audit log
   - Next cycle recommendation
3. Create export formats: Markdown, HTML, PDF, JSON, CSV
4. Create report versioning

### Acceptance Criteria

- [ ] Every completed run produces report
- [ ] Report understandable without reading logs
- [ ] Sources, evidence, decisions included
- [ ] Multiple export formats work

---

## Phase 24: Approval and Safety System

**Goal**: Make autonomy safe and governable.

### Tasks

1. Create approval request model and API
2. Create action classification:
   - Always allowed
   - Approval required
   - Never allowed
3. Create approval queue
4. Create approval workflow (approve/deny with reason)
5. Create budget enforcement
6. Create source compliance checks
7. Create safety settings per project

### Acceptance Criteria

- [ ] No external action without permission
- [ ] Restricted sources not scraped
- [ ] Budgets enforced
- [ ] Audit logs cannot be disabled

---

## Phase 25: Frontend — Project Setup

**Goal**: Initialize the Next.js frontend.

### Tasks

1. Create `frontend/package.json` with dependencies:
   - next, react, tailwindcss, @tanstack/react-query, recharts,
     react-markdown, lucide-react, clsx, tailwind-merge
2. Create `frontend/next.config.js`
3. Create `frontend/tailwind.config.js`
4. Create `frontend/tsconfig.json`
5. Create layout components:
   - Sidebar, Header, Footer
6. Create API client (`lib/api.ts`)
7. Create TypeScript types (`lib/types.ts`)
8. Create base page layout

### Acceptance Criteria

- [ ] Frontend starts with `npm run dev`
- [ ] Layout renders correctly
- [ ] API client configured
- [ ] Types match backend schemas

---

## Phase 26: Frontend — Project Dashboard

**Goal**: Project management UI.

### Tasks

1. Create project list page
2. Create project detail page
3. Create project creation form
4. Create project settings panel:
   - Domain/scope configuration
   - Idle settings
   - Budget settings
   - Approval settings
   - Safety settings
5. Create active runs view
6. Create project activity timeline

### Acceptance Criteria

- [ ] User can create, view, edit projects
- [ ] Settings panel works
- [ ] Active runs visible

---

## Phase 27: Frontend — Idea Ledger

**Goal**: Idea management UI.

### Tasks

1. Create idea ledger page (table with filters/sorting)
2. Create idea detail page:
   - Idea text and versions
   - Score breakdown
   - Classification history
   - Linked papers, clusters, conflicts
   - Research questions generated
   - Hypotheses
   - Validation plans
   - Decision history
3. Create idea comparison view
4. Create rejected ideas view with reasons
5. Create idea search

### Acceptance Criteria

- [ ] User can see all ideas
- [ ] Score breakdown visible
- [ ] Full idea history accessible
- [ ] Rejected ideas viewable with reasons

---

## Phase 28: Frontend — Literature and Research Views

**Goal**: Paper, cluster, conflict, question, hypothesis UIs.

### Tasks

1. Create paper table view with sorting/filtering
2. Create paper detail view
3. Create cluster map visualization
4. Create conflict view
5. Create research questions view
6. Create hypotheses view
7. Create validation plans view
8. Create research run timeline view
9. Create approval queue view

### Acceptance Criteria

- [ ] All views functional
- [ ] Data correctly displayed
- [ ] Navigation between views works

---

## Phase 29: Frontend — Skills, Reports, Wiki

**Goal**: Skill browser, reports, wiki UIs.

### Tasks

1. Create skill browser page
2. Create skill detail page:
   - Skill procedure
   - Performance metrics
   - Version history
   - Usage history
3. Create reports page
4. Create report detail view
5. Create research wiki page
6. Create wiki section navigation
7. Create report export buttons

### Acceptance Criteria

- [ ] Skill browser works
- [ ] Reports viewable and exportable
- [ ] Wiki readable and searchable

---

## Phase 30: Integration and End-to-End Testing

**Goal**: Connect all modules and verify complete workflows.

### Tasks

1. Connect prompt intake to orchestrator
2. Connect idle engine to scheduler
3. Connect literature engine to paper analysis
4. Connect paper analysis to clustering
5. Connect clustering to conflict detection
6. Connect conflicts to questions
7. Connect questions to hypotheses
8. Connect hypotheses to validation
9. Connect validation to scoring
10. Connect scoring to idea ledger
11. Connect research runs to skill memory
12. Connect all outputs to dashboard and reports
13. Create end-to-end test: user-directed research cycle
14. Create end-to-end test: idle citation-conflict cycle
15. Create end-to-end test: idea scoring and rejection
16. Create end-to-end test: skill creation and reuse
17. Run full regression tests

### Acceptance Criteria

- [ ] User-directed research works end-to-end
- [ ] Idle autonomous research works
- [ ] Idea scoring works
- [ ] Skill creation and reuse works
- [ ] Reports generated correctly
- [ ] Dashboard shows all data
- [ ] All tests pass

---

## Phase 31: Packaging and Deployment

**Goal**: Make the system installable.

### Tasks

1. Create Docker Compose setup (backend + frontend + PostgreSQL + Redis + sandbox)
2. Create local install script
3. Create environment template (.env.example with all required vars)
4. Create first-run setup wizard
5. Create model/API key configuration guide
6. Create database initialization script
7. Create example project with sample research run
8. Create troubleshooting guide
9. Create user documentation
10. Create developer documentation

### Acceptance Criteria

- [ ] User can install locally with Docker Compose
- [ ] User can create a project
- [ ] User can run a research cycle
- [ ] User can enable idle cognition
- [ ] Documentation complete

---

## Phase 32: Evaluation and Benchmarking

**Goal**: Prove the system works.

### Tasks

1. Create test idea set (10+ diverse research topics)
2. Create baseline: one-shot LLM idea generation
3. Create baseline: static literature review agent
4. Create cyclic agent evaluation
5. Compare novelty scores
6. Compare feasibility scores
7. Compare prior-art overlap
8. Compare validation-plan quality
9. Measure skill reuse improvement
10. Measure idle idea value
11. Generate benchmark report

### Acceptance Criteria

- [ ] System proves improvement over baselines
- [ ] Skill reuse measured
- [ ] Idle research value measured
- [ ] Benchmark report generated

---

## Implementation Order Summary

| Phase | Name | Estimated Effort |
|---|---|---|
| 1 | Repository & Documentation | 1-2 days |
| 2 | Backend Foundation | 3-5 days |
| 3 | Complete Data Model | 3-4 days |
| 4 | Research State & Audit | 2-3 days |
| 5 | LLM Provider Abstraction | 3-4 days |
| 6 | Academic Connectors | 4-5 days |
| 7 | Keyword Expansion | 2-3 days |
| 8 | Literature Retrieval | 3-4 days |
| 9 | Paper Analysis | 3-4 days |
| 10 | Clustering | 3-4 days |
| 11 | Conflict Detection | 3-4 days |
| 12 | Question Generation | 2-3 days |
| 13 | Hypothesis Generation | 2-3 days |
| 14 | Validation Planning | 2-3 days |
| 15 | Idea Scoring | 2-3 days |
| 16 | Idea Ledger | 2-3 days |
| 17 | Skill Memory | 3-4 days |
| 18 | Idle Cognition | 4-5 days |
| 19 | Agent Definitions | 3-4 days |
| 20 | Workflow Engine | 4-5 days |
| 21 | Data Analysis Sandbox | 3-4 days |
| 22 | Knowledge Base | 2-3 days |
| 23 | Reporting | 2-3 days |
| 24 | Approval & Safety | 2-3 days |
| 25 | Frontend Setup | 2-3 days |
| 26 | Frontend Projects | 3-4 days |
| 27 | Frontend Ideas | 3-4 days |
| 28 | Frontend Literature | 3-4 days |
| 29 | Frontend Skills/Reports | 3-4 days |
| 30 | Integration & E2E | 5-7 days |
| 31 | Packaging & Deploy | 3-4 days |
| 32 | Evaluation | 5-7 days |

**Total estimated**: ~90-120 working days for a solo developer

---

## Next Step

**Start Phase 1**: Create the repository structure, initialize git, create all documentation files, and set up the project foundation.

Shall I begin implementing Phase 1 now?
