# Technology Stack

**Analysis Date:** 2026-07-09

## Languages

**Primary:**
- Python 3.11+ — Backend API, research engines, orchestrators
- TypeScript 5.x — Frontend React components and hooks

**Secondary:**
- SQL (PostgreSQL dialect) — Database queries, migrations
- CSS/Tailwind — Styling
- YAML — Docker Compose, CI config

## Runtime

**Environment:**
- Python 3.11+ with asyncio
- Node.js 18+ for frontend build

**Package Managers:**
- Python: `uv` (fast pip-compatible resolver) + `hatch` build system (`backend/pyproject.toml`)
- Frontend: npm (`frontend/package.json`) and pnpm (used in some external tools)

## Frameworks

**Core:**
- FastAPI 0.110+ — REST API framework with async support
- Next.js 14.2 — React framework with App Router
- SQLAlchemy 2.0+ — Async ORM with asyncpg driver
- Pydantic 2.5+ — Data validation with `model_dump` (v2 API)

**Frontend:**
- React 18.x — UI library
- Tailwind CSS 3.x — Utility-first styling
- next-themes — Dark/light mode
- lucide-react — Icon library
- recharts — Charting

**Testing:**
- pytest 8.0+ — Python test runner
- pytest-asyncio — Async test support
- pytest-cov — Coverage reports
- vitest — Frontend unit tests (TypeScript)
- Playwright — E2E browser tests

**Build/Dev:**
- hatch — Python packaging
- Next.js build system — Frontend compilation
- Alembic — Database migrations
- ruff — Python linting and formatting

## Key Dependencies

**Backend Python:**
- httpx — Async HTTP client for API calls
- redis[hiredis] — Redis client (async)
- asyncpg — PostgreSQL async driver
- structlog — Structured JSON logging
- pydantic-settings — Environment-based config
- sentence-transformers — Embedding generation (for wiki/paper search)
- Jinja2 — Template rendering (LaTeX templates)
- python-multipart — File upload support
- python-jose — JWT token handling
- passlib — Password hashing (encrypted vault)
- cryptography — AES-GCM encryption for API key vault
- pytest-asyncio — async test support

**Frontend:**
- next 14.2 — React framework
- react 18.x — UI
- lucide-react — Icons
- recharts — Charts
- vitest — TypeScript testing

## Infrastructure

**Databases:**
- PostgreSQL 14+ — Relational database
- Redis 5+ — Cache + pub/sub

**Containerization:**
- Docker — Service containerization
- Docker Compose — Multi-service orchestration

**CI/CD:**
- GitHub Actions — CI pipeline

## Configuration

**Environment:** `.env` file with pydantic-settings (`backend/app/config.py`)

**Build:** Alembic for database migrations, ruff for linting

## Platform Requirements

**Development:**
- PostgreSQL 14+ for database
- Redis 5+ for caching/pubsub
- Node.js 18+ for frontend
- Python 3.11+ for backend

**Production:**
- Docker + Docker Compose
- PostgreSQL 14+
- Redis 5+
- (Optional) pdflatex for PDF compilation
- (Optional) pandoc for DOCX export

*Stack analysis: 2026-07-09*
