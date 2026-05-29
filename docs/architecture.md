# Architecture

## System Overview

The Background Scientific Cognition System is a long-running autonomous research platform. It accepts user research ideas, monitors scientific literature, generates hypotheses from conflicts, scores ideas, and learns reusable research skills.

---

## Architectural Principles

1. **Database-first** — all state lives in PostgreSQL, not chat history
2. **Audit-everything** — every action, decision, and tool call is logged
3. **Provider-agnostic LLM** — abstract LLM providers behind a common interface
4. **Workflow-durable** — research workflows can pause, resume, and survive failures
5. **Sandbox-safe** — data analysis runs in isolated Docker containers
6. **Skill-learning** — the system improves by converting experience into reusable skills

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│              (Next.js / React / Tailwind)                │
├─────────────────────────────────────────────────────────┤
│                    REST API Layer                        │
│                   (FastAPI Routes)                       │
├─────────────────────────────────────────────────────────┤
│                    Service Layer                         │
│         (Business Logic / Orchestration)                 │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│ Agents   │ Engines  │ Workflow │ LLM      │ Connectors  │
│ (15      │ (Core    │ (Durable │ (Multi-  │ (Academic   │
│  roles)  │  logic)  │  state)  │ provider)│  sources)   │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│                    Data Layer                            │
│         (SQLAlchemy + PostgreSQL + pgvector)             │
├─────────────────────────────────────────────────────────┤
│                 Infrastructure                           │
│     (Redis, Docker Sandbox, Scheduler)                   │
└─────────────────────────────────────────────────────────┘
```

---

## Major Components

### 1. User Interface

Next.js web dashboard with 15+ views:

- Project dashboard
- Active research run timeline
- Idea ledger with score breakdown
- Paper table with sorting/filtering
- Cluster/conflict visualization
- Research questions and hypotheses
- Validation plans
- Skill memory browser
- Research wiki
- Report viewer
- Approval queue
- Project settings

### 2. Project Manager

Stores each project's configuration:

- Domain and subject scope
- Out-of-scope areas
- Default flexibility level
- Idle research settings (enabled, trigger time, budget)
- Source allowlist
- Budget limits
- Approval requirements
- Safety settings

### 3. Research Orchestrator

Coordinates all agents, workflows, states, and approvals:

- Starts and resumes research runs
- Assigns tasks to agents
- Enforces budgets
- Routes tool calls
- Pauses for approval
- Logs every state transition
- Generates final reports

### 4. Autonomy and Flexibility Engine

Determines how much freedom the system has:

| Flexibility | Behavior |
|---|---|
| 0.0 | Strict execution — follow user idea exactly |
| 0.25 | Minor refinement allowed |
| 0.50 | Adjacent pivot allowed |
| 0.75 | Major reframing allowed if justified |
| 1.0 | Agent chooses best direction independently |

### 5. Idle Cognition Engine

Runs during idle periods with weighted mode selection:

- 35% Literature frontier scan
- 25% Citation-conflict question generation
- 15% Revisit rejected ideas with new literature
- 10% Cross-domain collision idea generation
- 10% Skill improvement
- 5% Dataset discovery

### 6. Literature Intelligence Engine

Searches, retrieves, ranks, and analyzes academic literature.

**Data Sources (ordered by priority):**

1. OpenAlex (free, comprehensive)
2. Semantic Scholar (free tier)
3. Crossref (free)
4. arXiv (free)
5. PubMed / Europe PMC (free)
6. DOAJ / CORE / Unpaywall
7. Publisher APIs (if allowed)

**Search Types:**

- High-impact papers (last 5 years)
- Frontier papers (last 6-12 months)
- Review/survey papers
- Contradictory papers
- Dataset/benchmark papers
- Adjacent-field papers

### 7. Paper Ingestion and Parsing Engine

Extracts structured information from papers:

- Problem, method, dataset, metrics
- Findings, limitations, future work
- Assumptions, key claims
- Relation to current idea

### 8. Paper Clustering Engine

Groups papers into themes:

- Topic clusters
- Method clusters
- Dataset clusters
- Claim/finding clusters

### 9. Conflict and Gap Detection Engine

Detects scientific tensions:

| Conflict Type | Description |
|---|---|
| Finding | Papers report different results |
| Method | Different methods solve the same problem |
| Dataset | Results depend on dataset/sample |
| Metric | Papers optimize different metrics |
| Assumption | Papers rely on incompatible assumptions |
| Scope | Method works only in narrow conditions |
| Theory-practice | Strong theory but weak deployment evidence |
| Recency | New work challenges older consensus |
| Replication | Results not reproduced across studies |

### 10. Research Question Generator

Derives questions from conflicts and gaps using templates:

- "Why do papers using [method A] find [result X] while papers using [method B] find [result Y]?"
- "Does [method] still work under [new condition]?"
- "Is the improvement caused by [mechanism] or by [dataset artifact]?"
- "Can [method from adjacent field] solve [repeated limitation]?"

### 11. Hypothesis Generator

Converts questions into testable hypotheses with:

- Statement, independent/dependent variables
- Context, baseline, metric
- Expected direction, failure condition

### 12. Validation Planner

Designs how to test hypotheses:

- Dataset candidates, baselines, metrics
- Experimental design, statistical tests
- Cost and feasibility estimates

### 13. Idea Scoring Engine

Scores ideas on 12 criteria (0-10) with weighted formula:

```
Overall Value =
  0.18 × Novelty + 0.14 × Feasibility + 0.14 × Importance
  + 0.12 × Evidence Support + 0.14 × Validation Clarity
  + 0.12 × Differentiation + 0.08 × Data Availability
  + 0.05 × Skill Leverage + 0.03 × User Alignment
  - 0.15 × Prior-Art Risk - 0.05 × Safety Risk
  - 0.03 × Cost Risk
```

### 14. Idea Ledger

Permanent memory of all ideas:

- Versions, scores, classifications
- Decisions and rejection reasons
- Linked papers, conflicts, hypotheses
- Revival when new evidence appears

### 15. Skill Memory

Learns reusable research methods:

**Skill Types:**

- Planning: high-level research strategies
- Functional: reusable multi-step workflows
- Atomic: small tool-use procedures
- Domain: field-specific heuristics
- Evaluation: scoring and classification rules
- Data: reusable analysis scripts
- Reporting: templates and structures
- Safety: hallucination/misuse prevention rules

**Lifecycle:**

```
Candidate → Tested → Active → Revised → Deprecated → Retired
```

### 16. Knowledge Base / Research Wiki

Readable persistent memory generated from structured data:

- Project overview, active themes
- Literature maps, important papers
- Open conflicts, research questions
- Active/rejected/validated hypotheses
- Skills, datasets, reports
- Decision history

### 17. Multi-Agent Runtime

15 specialized agents with defined roles:

| Agent | Responsibility |
|---|---|
| Orchestrator | Controls run flow, tracks state, assigns tasks |
| User Intent | Interprets prompts, determines flexibility |
| Idle Cognition | Runs background research cycles |
| Literature | Searches academic sources |
| Paper Analyst | Extracts structured claims from papers |
| Cluster | Groups papers into themes |
| Conflict | Detects scientific tensions |
| Research Question | Generates questions from conflicts |
| Hypothesis | Forms testable hypotheses |
| Validation Planner | Designs experiments |
| Data Analyst | Runs sandboxed analysis |
| Skeptic | Challenges novelty and feasibility |
| Decision | Chooses next action |
| Skill Curator | Creates and updates skills |
| Archivist | Documents everything |

### 18. Tool Gateway

Unified interface for all external tools and APIs:

- Academic source connectors
- LLM providers
- Sandbox executor
- Search tools
- Export tools

### 19. Permissions and Safety Layer

Three-tier permission model:

- **Always allowed**: search APIs, generate ideas, write reports
- **Approval required**: email, publish, spend money
- **Never allowed**: bypass paywalls, fabricate citations, hide failures

### 20. Logging and Audit System

Complete audit trail:

- Every state transition
- Every tool call with input/output
- Every decision with reasoning
- Every score with justification
- Every approval with reason

---

## Data Flow

### User-Directed Research

```
User Prompt
→ Intent Analysis (strict/flexible)
→ Search Planning
→ Literature Retrieval
→ Paper Analysis
→ Clustering
→ Conflict Detection
→ Question Generation
→ Hypothesis Formation
→ Validation Planning
→ Idea Scoring
→ Classification
→ Skill Creation
→ Report Generation
→ Wiki Update
```

### Idle Cognition

```
Idle Trigger (project active, user inactive)
→ Mode Selection (weighted random)
→ [Mode-specific workflow]
→ Idea Scoring
→ Classification
→ Skill Creation
→ Report Generation
→ Wiki Update
```

---

## Technology Decisions

| Decision | Choice | Reasoning |
|---|---|---|
| Language | Python | Best ecosystem for AI, academic APIs, scientific computing |
| Web Framework | FastAPI | Async, fast, auto-docs, Pydantic integration |
| Database | PostgreSQL | Reliable, JSON support, pgvector for embeddings |
| ORM | SQLAlchemy | Mature, flexible, async support via asyncpg |
| Migrations | Alembic | Standard for SQLAlchemy projects |
| Cache/Queue | Redis | Fast, reliable, supports Celery/Dramatiq |
| LLM | Multi-provider | Flexibility, cost control, fallback capability |
| Agent Runtime | LangGraph-style | Durable, stateful, resumable workflows |
| Frontend | Next.js | React SSR, great DX, Tailwind integration |
| Sandbox | Docker | Safe code execution, reproducible environments |
| Embeddings | pgvector or Qdrant | Vector search for papers, notes, skills |
