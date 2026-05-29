# Autoscience - User Guide

## How to Run the Project

### Option 1: Docker Compose (Recommended)

```bash
cd /mnt/windowsd/PythonProjects/mbmbb/autoscience

# Start all services
docker-compose -f docker/docker-compose.yml up

# Access:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Development Mode

**Terminal 1 — Backend:**

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev,sandbox]"

# Configure API keys
cp .env.example .env
# Edit .env and add your API keys

# Start PostgreSQL (or use Docker)
docker run -d --name postgres -p 5432:5432 \
  -e POSTGRES_DB=autoscience \
  -e POSTGRES_USER=autoscience \
  -e POSTGRES_PASSWORD=autoscience \
  postgres:15-alpine

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### Option 3: One-Command Install

```bash
cd /mnt/windowsd/PythonProjects/mbmbb/autoscience
./install.sh
```

---

## Configuration

**Edit `backend/.env`:**

```env
# Required: At least one LLM provider
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Optional: Local LLM
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=llama3

# Database
DATABASE_URL=postgresql+asyncpg://autoscience:autoscience@localhost:5432/autoscience

# Academic API keys (optional, improves rate limits)
SEMANTIC_SCHOLAR_API_KEY=your-key
UNPAYWALL_EMAIL=your@email.com
```

---

## First Research Run

1. Open http://localhost:3000
2. Click **Create Project**
3. Enter a name and domain (e.g., "AI Research", "Machine Learning")
4. Click **New Research Run**
5. Enter your idea (e.g., "Using attention mechanisms for time series forecasting")
6. Watch the system research your idea!

---

## Troubleshooting

**Database connection error:**
```bash
# Make sure PostgreSQL is running
docker ps | grep postgres

# Check connection
psql -h localhost -U autoscience -d autoscience
```

**API key errors:**
```bash
# Verify .env file
cat backend/.env | grep API_KEY
```

**Port conflicts:**
```bash
# Check what's using port 8000
lsof -i :8000

# Use different port
uvicorn app.main:app --port 8001
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Interface                              │
│               (Next.js React Dashboard)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Layer                                   │
│                (FastAPI REST Endpoints)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Research Orchestrator                           │
│            (Coordinates all research modules)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ LLM Router    │    │  Connectors   │    │   Sandbox     │
│ (Multi-       │    │ (5 Academic   │    │ (Docker       │
│  Provider)    │    │  Sources)     │    │  Execution)   │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Research Engines                             │
│  Keyword → Literature → Analysis → Clustering → Conflicts       │
│  Questions → Hypotheses → Validation → Scoring → Skills         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                             │
│              (30+ tables, full audit trail)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Features

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
