# Autoscience

> A persistent, autonomous research platform that works like a researcher's second brain.

Autoscience is a **Background Scientific Cognition System**. It takes a research
idea (or runs autonomously while you're idle), then drives it through a full
research loop: literature retrieval, clustering, conflict detection, question
and hypothesis generation, validation planning, analysis, scoring, and reporting
— while keeping a complete audit trail and a reusable library of research skills.

---

## Why Autoscience?

- **Persistent memory** — every idea, paper, hypothesis, and rejected attempt is
  stored, not discarded.
- **Autonomous idle research** — keeps working in the background when you're away,
  across six research modes (frontier scan, citation-conflict, cross-domain, …).
- **Multi-source literature** — pulls from OpenAlex, Semantic Scholar, Crossref,
  arXiv, PubMed, DOAJ, Unpaywall, and more.
- **Governance built in** — permission model, budget enforcement, source
  allow/deny lists, and human approval gates for sensitive actions.
- **Reusable skills** — successful research patterns are distilled into skills
  that future runs can invoke.

---

## Features

### Research pipeline
- **Literature search & analysis** across 5+ academic sources with structured extraction.
- **Clustering** of papers into themes and **conflict detection** between findings.
- **Question generation** from detected conflicts and **hypothesis formation**.
- **Validation planning** (experiments, power analysis, effect-size extraction).
- **Idea scoring** across 12 dimensions and a full **idea ledger**.
- **Manuscript generation** with LaTeX rendering, journal templates, and citation graphs.
- **Peer review** proposals and a revision workflow.

### Autonomous & collaborative
- **Idle cognition** with configurable budget/time limits and lock-safe scheduling.
- **Organizations, teams, and RBAC** (roles, permissions, audit logs).
- **Wiki** with semantic embeddings and a knowledge graph.
- **Activity feed, notifications, and OAuth** (Google, GitHub).
- **Datasets** ingestion and provenance tracking (Kaggle, uploads).

### Safety & governance
- Permission tiers: *always allowed*, *approval required*, *never allowed*.
- Per-run and daily budget enforcement.
- Source compliance and an explicit approval workflow for sensitive operations.

---

## Architecture

| Layer | Stack |
|-------|-------|
| **Backend** | Python · FastAPI · SQLAlchemy · PostgreSQL (+ pgvector) · Redis · Alembic |
| **LLM providers** | OpenAI · Anthropic · OpenRouter · Local (Ollama/vLLM) · llama.cpp |
| **Academic sources** | OpenAlex · Semantic Scholar · Crossref · arXiv · PubMed · DOAJ · Unpaywall · Firecrawl |
| **Frontend** | Next.js · React · TypeScript · Tailwind CSS · React Query · Recharts · Lucide |
| **Sandbox** | Docker-based code execution |
| **Tests** | pytest (backend) · Vitest + Playwright (frontend) |
| **CI** | GitHub Actions |

```
User Prompt or Idle Trigger
  → Autonomy / Flexibility decision
  → Literature retrieval
  → Paper clustering
  → Conflict detection
  → Research question generation
  → Hypothesis generation
  → Validation planning
  → Data analysis
  → Idea scoring
  → Idea ledger
  → Skill creation & reuse
  → Report & wiki update
```

---

## Quick start

### Prerequisites
- Docker & Docker Compose
- (Dev mode only) Python 3.11+ and Node.js 20+

### Docker (recommended)

```bash
# 1. Create your .env (API keys etc.) — see Configuration
cp backend/.env.example backend/.env
#    edit backend/.env and add at least one LLM provider key

# 2. Start everything
./start.sh docker

# 3. Open the app
#    Frontend: http://localhost:3000
#    Backend API docs: http://localhost:8000/docs
```

Useful commands: `./start.sh stop`, `./start.sh status`, `./start.sh logs`,
`./start.sh dev` (development mode with hot-reload).

### Manual / development mode

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,sandbox]"
cp .env.example .env          # add your API keys
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Configuration

Copy `backend/.env.example` to `backend/.env` and fill in the values. The most
important settings:

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY` | LLM provider keys (at least one) |
| `DEFAULT_LLM_PROVIDER` | Which provider to use by default |
| `LOCAL_LLM_BASE_URL` | Base URL for a local model (Ollama/vLLM) |
| `POSTGRES_PASSWORD`, `POSTGRES_PORT` | Database |
| `REDIS_PORT`, `REDIS_CLUSTER_NODES` | Cache / pub-sub |
| `SEMANTIC_SCHOLAR_API_KEY`, `UNPAYWALL_EMAIL` | Higher rate limits for sources |
| `GOOGLE_OAUTH_CLIENT_ID/SECRET`, `GITHUB_OAUTH_CLIENT_ID/SECRET` | Optional auth |

> Secrets live only in `.env`, which is gitignored. Never commit real keys.

---

## Project structure

```
autoscience/
├── backend/
│   ├── app/
│   │   ├── agents/        # Specialized research agents
│   │   ├── api/           # REST API endpoints (FastAPI routers)
│   │   ├── connectors/    # Academic-source connectors
│   │   ├── engine/        # Research & manuscript engines
│   │   ├── llm/           # LLM provider abstractions + router
│   │   ├── middleware/    # Auth/RBAC middleware
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── workflows/     # Workflow & safety-gate definitions
│   │   ├── sandbox/       # Docker code-execution sandbox
│   │   └── utils/         # Helpers (redis, sanitization, json)
│   ├── alembic/           # Database migrations
│   ├── scripts/           # Operational scripts
│   └── tests/             # pytest suite
├── frontend/
│   └── src/
│       ├── app/           # Next.js routes/pages
│       ├── components/    # React components
│       ├── hooks/         # Custom hooks
│       └── lib/           # API client & types
├── docker/                # Docker / compose configs
├── docs/                  # Architecture, data model, roadmap, safety policy
└── start.sh               # One-command start/stop script
```

---

## Development

```bash
# Backend tests & quality
cd backend
pytest
ruff check .
ruff format .
mypy app/

# Frontend tests
cd frontend
npm test              # Vitest unit tests
npm run test:e2e      # Playwright end-to-end (requires running app)
```

Database schema changes use Alembic:

```bash
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

---

## API overview

The REST API is served under `/api/v1`. Notable groups:

| Group | Examples |
|-------|----------|
| Research | `POST /api/v1/research/run`, `POST /api/v1/research/idle` |
| Projects | `GET/POST /api/v1/projects`, `GET/PUT/DELETE /api/v1/projects/{id}` |
| Ideas | `GET/POST /api/v1/ideas`, `GET/PUT /api/v1/ideas/{id}` |
| Papers | `GET/POST /api/v1/papers`, `GET /api/v1/papers/{id}` |
| Skills | `GET/POST /api/v1/skills`, `GET /api/v1/skills/{id}` |
| Manuscripts | `POST /api/v1/manuscripts`, download/export |
| Collaboration | organizations, teams, peer review, RBAC |

Interactive docs are available at `/docs` (Swagger) and `/redoc` when the
backend is running.

---

## License

Released under the [MIT License](LICENSE).

---

## Acknowledgments

Built with reference to:
ScienceClaw · DeerFlow · freephdlabor · Agent Laboratory · SkillX · Open Collider ·
WeKnora · PhysicsIntern.
