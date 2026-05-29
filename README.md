# Background Scientific Cognition System

A persistent, autonomous research platform that functions like a researcher's brain — monitoring scientific literature, generating ideas during idle time, detecting conflicts, forming hypotheses, analyzing evidence, scoring ideas, rejecting weak directions, and learning reusable research skills from every cycle.

---

## What This System Does

1. **Accepts user research ideas** and researches them thoroughly
2. **Detects user flexibility** — follows strict prompts narrowly, adapts flexible ideas when evidence supports better directions
3. **Starts autonomous idle research** when the project is active but no user task is running
4. **Monitors recent scientific literature** from multiple academic sources
5. **Clusters papers into themes** and detects scientific tensions, conflicts, assumptions, and gaps
6. **Generates research questions** from those conflicts
7. **Converts questions into testable hypotheses** with variables, baselines, and failure conditions
8. **Designs validation plans** with datasets, metrics, and experimental design
9. **Analyzes data** in a sandboxed environment when appropriate
10. **Scores and classifies every idea** — high-value, promising, incremental, weak, or reject
11. **Stores every idea, including rejected ones**, with reasons
12. **Creates reusable research skills** from successful and failed cycles
13. **Uses those skills** in future research
14. **Maintains a full audit trail** of what it tried, why, what happened, and what decision it made

---

## Core Differentiator

This is not just "automated research." The distinctive properties are:

- **User-flexibility-aware autonomy** — changes behavior based on whether the user gives a strict prompt, a flexible idea, or no idea at all
- **Idle scientific cognition** — autonomously scans literature and generates research questions during idle periods
- **Conflict-driven question generation** — identifies conflicts, gaps, and unresolved tensions in the literature rather than generating random ideas
- **Idea ledger with rejection memory** — stores all ideas, including bad ones, with scores and rejection reasons
- **Skill memory** — learns reusable research procedures from previous cycles and applies them to future work

---

## Central Loop

```
Observe → Assimilate → Cluster → Detect Tension → Ask Questions
→ Form Hypotheses → Validate → Judge → Remember → Learn → Repeat
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL, pgvector/Qdrant |
| Cache/Queue | Redis, Celery/Dramatiq |
| LLM Providers | OpenAI, Anthropic, Local (Ollama/vLLM) |
| Agent Runtime | LangGraph-style durable workflows |
| Frontend | Next.js, React, Tailwind CSS |
| Data Analysis | Docker sandbox, Pandas, NumPy, SciPy, scikit-learn |
| Academic Sources | OpenAlex, Semantic Scholar, Crossref, arXiv, PubMed |

---

## Project Structure

```
autoscience/
├── docs/                    # Architecture, data model, API design, policies
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── models/          # SQLAlchemy database models
│   │   ├── schemas/         # Pydantic validation schemas
│   │   ├── api/             # REST API endpoints
│   │   ├── services/        # Business logic
│   │   ├── agents/          # Specialized research agents
│   │   ├── llm/             # LLM provider abstraction
│   │   ├── connectors/      # Academic source connectors
│   │   ├── engine/          # Core research engines
│   │   ├── workflows/       # Durable research workflows
│   │   ├── sandbox/         # Data analysis sandbox
│   │   └── utils/           # Shared utilities
│   └── tests/               # Test suite
├── frontend/                # Next.js web dashboard
│   └── src/
│       ├── app/             # Next.js pages
│       ├── components/      # React components
│       └── lib/             # API client, types
├── docker/                  # Docker configurations
├── .env.example             # Environment template
└── IMPLEMENTATION_PLAN.md   # Detailed build plan
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker (for sandbox execution)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd autoscience

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
vim .env

# Start infrastructure
docker compose -f docker/docker-compose.yml up -d

# Install backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run database migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload

# Install frontend (in separate terminal)
cd frontend
npm install
npm run dev
```

### First Run

1. Open http://localhost:3000
2. Create a new project with domain and scope
3. Submit a research idea
4. Watch the system research it

---

## Development

```bash
# Run backend tests
cd backend
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run frontend lint
cd frontend
npm run lint
```

---

## Documentation

- [Architecture](docs/architecture.md) — System design and component overview
- [Data Model](docs/data-model.md) — Database schema and relationships
- [API Design](docs/api-design.md) — REST API endpoints and contracts
- [Safety Policy](docs/safety-policy.md) — Permissions, approvals, and restrictions
- [Development Standards](docs/development-standards.md) — Code quality and conventions
- [Roadmap](docs/roadmap.md) — Development phases and milestones
- [Implementation Plan](IMPLEMENTATION_PLAN.md) — Detailed build plan with all phases

---

## License

TBD
