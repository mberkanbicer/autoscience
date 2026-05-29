# Autoscience

A persistent, autonomous research platform that functions like a researcher's brain.

## What is Autoscience?

Autoscience is a Background Scientific Cognition System that:

- Accepts user research ideas and researches them thoroughly
- Detects user flexibility and adapts accordingly
- Starts autonomous idle research during inactive periods
- Monitors recent scientific literature from multiple sources
- Clusters papers into themes and detects conflicts
- Generates research questions from those conflicts
- Converts questions into testable hypotheses
- Designs validation plans with experiments
- Scores and classifies every idea
- Stores all ideas including rejected ones with reasons
- Creates reusable research skills from cycles
- Maintains a full audit trail

## Quick Start

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

# Run installation script
./install.sh

# Or install manually:

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,sandbox]"

# Frontend
cd frontend
npm install
```

### Configuration

1. Copy the environment template:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Edit `backend/.env` with your API keys:
   ```
   OPENAI_API_KEY=your-key-here
   ANTHROPIC_API_KEY=your-key-here
   ```

### Running

**Development mode:**

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

**Docker mode:**

```bash
docker-compose -f docker/docker-compose.yml up
```

### Access

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

---

## Architecture

### Backend (Python/FastAPI)

- **Database**: PostgreSQL with SQLAlchemy
- **LLM Providers**: OpenAI, Anthropic, Local (Ollama/vLLM)
- **Academic Sources**: OpenAlex, Semantic Scholar, Crossref, arXiv, PubMed
- **Agent Runtime**: Custom workflow engine with 15 specialized agents
- **Sandbox**: Docker-based code execution

### Frontend (Next.js/React)

- **UI Framework**: Tailwind CSS
- **State Management**: React Query
- **Charts**: Recharts
- **Icons**: Lucide React

### Core Loop

```
User Prompt or Idle Trigger
→ Autonomy/Flexibility Decision
→ Literature Retrieval
→ Paper Clustering
→ Conflict Detection
→ Research Question Generation
→ Hypothesis Generation
→ Validation Planning
→ Data Analysis
→ Idea Scoring
→ Idea Ledger
→ Skill Creation & Reuse
→ Report & Wiki Update
```

---

## Features

### Research Capabilities

- **Literature Search**: Search 5+ academic sources
- **Paper Analysis**: Extract structured information
- **Clustering**: Group papers by theme
- **Conflict Detection**: Find scientific tensions
- **Question Generation**: Derive research questions
- **Hypothesis Formation**: Create testable hypotheses
- **Validation Planning**: Design experiments
- **Idea Scoring**: Evaluate on 12 dimensions

### Autonomous Research

- **Idle Cognition**: Background research during idle periods
- **6 Research Modes**: Frontier scan, citation conflict, cross-domain, etc.
- **Budget Control**: Automatic cost and time limits
- **Skill Learning**: Reusable research methods

### Knowledge Management

- **Idea Ledger**: Store all ideas with history
- **Research Wiki**: Auto-generated documentation
- **Skill Memory**: Learn from successful cycles
- **Audit Trail**: Complete logging of all actions

### Safety and Governance

- **Permission Model**: Always allowed, approval required, never allowed
- **Budget Enforcement**: Per-run and daily limits
- **Source Compliance**: Allowed/blocked academic sources
- **Approval Workflow**: User approval for sensitive actions

---

## Project Structure

```
autoscience/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── api/             # REST API endpoints
│   │   ├── services/        # Business logic
│   │   ├── agents/          # 15 specialized agents
│   │   ├── llm/             # LLM providers
│   │   ├── connectors/      # Academic source connectors
│   │   ├── engine/          # Research engines
│   │   ├── workflows/       # Workflow definitions
│   │   └── sandbox/         # Code execution sandbox
│   └── tests/               # Test suite
├── frontend/
│   └── src/
│       ├── app/             # Next.js pages
│       ├── components/      # React components
│       └── lib/             # API client, types
├── docker/                  # Docker configurations
└── docs/                    # Documentation
```

---

## API Reference

### Research Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/research/run` | Start a research run |
| POST | `/api/v1/research/idle` | Start an idle cycle |

### Project Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/projects` | List projects |
| POST | `/api/v1/projects` | Create project |
| GET | `/api/v1/projects/{id}` | Get project |
| PUT | `/api/v1/projects/{id}` | Update project |
| DELETE | `/api/v1/projects/{id}` | Delete project |

### Idea Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ideas` | List ideas |
| POST | `/api/v1/ideas` | Create idea |
| GET | `/api/v1/ideas/{id}` | Get idea |
| PUT | `/api/v1/ideas/{id}` | Update idea |

### Paper Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/papers` | List papers |
| POST | `/api/v1/papers` | Create paper |
| GET | `/api/v1/papers/{id}` | Get paper |

### Skill Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/skills` | List skills |
| POST | `/api/v1/skills` | Create skill |
| GET | `/api/v1/skills/{id}` | Get skill |

---

## Development

### Running Tests

```bash
cd backend
pytest
```

### Code Style

```bash
cd backend
ruff check .
ruff format .
```

### Type Checking

```bash
cd backend
mypy app/
```

---

## License

MIT License

---

## Acknowledgments

Built with reference to:

- ScienceClaw - Research memory and skills
- DeerFlow - Long-horizon orchestration
- freephdlabor - Scientific lifecycle
- Agent Laboratory - Research workflow
- SkillX - Skill learning
- Open Collider - Cross-domain ideation
- WeKnora - Knowledge base
- PhysicsIntern - Structured research state
