# External Integrations

**Analysis Date:** 2026-07-09

## Academic Literature APIs

### Semantic Scholar
- Purpose: Paper search, citations, references, metadata
- SDK: `semanticscholar>=0.4.0`, custom connector in `connectors/semantic_scholar.py`
- Auth: `SEMANTIC_SCHOLAR_API_KEY` (optional, for higher rate limits)

### arXiv
- Purpose: Free academic papers, recent papers by category
- SDK: Native httpx client
- Auth: None (public API)

### OpenAlex
- Purpose: Academic works, authors, venues (from Microsoft Academic Graph)
- SDK: Native httpx client
- Auth: `OPENALEX_EMAIL` for rate limiting

### Crossref
- Purpose: DOI resolution, metadata, citations, references
- SDK: Native httpx client
- Auth: Email for rate limiting

### PubMed
- Purpose: Medical and life sciences literature
- SDK: Native httpx client with XML parsing
- Auth: `PUBMED_API_KEY` (optional)

### DOAJ
- Purpose: Directory of Open Access Journals
- SDK: Native httpx client
- Auth: None (public API)
- Location: `backend/app/connectors/doaj.py`

### CORE
- Purpose: Aggregated open access papers
- SDK: Native httpx client
- Auth: `CORE_API_KEY` required
- Location: `backend/app/connectors/core.py`

### Unpaywall
- Purpose: DOI lookup, open access status
- SDK: Native httpx client
- Auth: Email for rate limiting
- Location: `backend/app/connectors/unpaywall.py`

### SearXNG (optional)
- Purpose: Federated web search for academic content
- SDK: Native httpx client
- Auth: None (requires `SEARXNG_URL` config)
- Location: `backend/app/connectors/searxng.py`

### Firecrawl (optional)
- Purpose: Web scraping for full-text extraction
- SDK: Native httpx client
- Auth: `FIRECRAWL_API_KEY` required
- Location: `backend/app/connectors/firecrawl.py`

## Dataset Repositories

### HuggingFace
- Purpose: Search datasets via HuggingFace Datasets API
- Location: `backend/app/connectors/dataset_connectors.py`

### Zenodo
- Purpose: Search Zenodo records for datasets
- Location: `backend/app/connectors/dataset_connectors.py`

### Kaggle
- Purpose: Dataset search (placeholder implementation)
- Location: `backend/app/connectors/dataset_connectors.py`

## LLM Providers

### OpenAI
- SDK: `openai>=1.12.0`
- Auth: `OPENAI_API_KEY`
- Default model: `gpt-4o` (configurable via `OPENAI_DEFAULT_MODEL`)

### Anthropic
- SDK: `anthropic>=0.18.0`
- Auth: `ANTHROPIC_API_KEY`
- Default model: `claude-sonnet-4-20250514`

### OpenRouter
- SDK: httpx via LLM router
- Auth: `OPENROUTER_API_KEY`
- Provider: Unified API for multiple LLMs

### Local (Ollama)
- Location: `backend/app/llm/local_provider.py`
- Default URL: `http://localhost:11434`
- Auth: None (local server)

### Llama.cpp
- Location: `backend/app/llm/llamacpp_provider.py`
- Default URL: `http://localhost:8080`
- Auth: None (local server)

## Data Storage

**PostgreSQL 14+** — Primary relational database
- Connection: `DATABASE_URL` (format: `postgresql+asyncpg://...`)
- Client: SQLAlchemy 2.0 async with asyncpg driver
- Migrations: Alembic in `backend/alembic/`
- Extensions: pgvector for embedding similarity search

**Redis** — Caching and pub/sub
- Connection: `REDIS_URL`
- Optional cluster support: `REDIS_CLUSTER_NODES`
- Uses: API response caching (CacheService), SSE event broadcasting (EventBroadcaster), idle scheduler locking

**File Storage:** Local filesystem only (no external blob storage)

## Authentication & Identity

**Auth Methods:**
- JWT Bearer tokens (primary) — generated via `POST /api/v1/auth/token`
- `X-User-Email` / `X-User-Name` headers (local/dev fallback)
- OAuth: Google (`/api/v1/auth/oauth/google`) and GitHub (`/api/v1/auth/oauth/github`)

**Implementation:**
- `backend/app/services/auth_service.py` — token creation/validation
- `backend/app/services/oauth_service.py` — OAuth flow handling
- `backend/app/dependencies/auth.py` — FastAPI dependency injection

## Monitoring & Observability

**Logging:** structlog for structured JSON logging across all services

**Error Tracking:** None (relies on logging)

**Real-time Events:** Redis pub/sub → SSE streaming to frontend
- Workflow events: `/api/v1/search/stream/{run_id}`
- Skill evaluation events: `/api/v1/skills/performance/eval-stream`

## CI/CD & Deployment

**Hosting:** Docker containers (`docker/Dockerfile`, `docker/docker-compose.yml`, `docker/docker-compose.dev.yml`)

**CI Pipeline:** GitHub Actions (`.github/workflows/ci.yml`)
- Trigger: Push/PR to main
- Steps: Build, test, verify migrations

## Communication

**Email (optional):** SMTP configured via `SMTP_*` env vars for review assignment notifications
- Location: `backend/app/services/notification_service.py`

## Frontend Integrations

**Libraries:**
- next-themes (dark/light mode)
- lucide-react (icons)
- recharts (charts in SkillPerformanceChart)
- vitest (unit tests)
- Playwright (E2E tests)

## Environment Configuration

**Required:**
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection

**Optional:**
- `OPENAI_API_KEY` — OpenAI authentication
- `ANTHROPIC_API_KEY` — Anthropic authentication
- `OPENROUTER_API_KEY` — OpenRouter authentication
- `SEMANTIC_SCHOLAR_API_KEY` — Higher rate limits
- `FIRECRAWL_API_KEY` — Web scraping
- `CORE_API_KEY` — CORE API access
- `SEARXNG_URL` — Federated search instance
- `SMTP_*` — Email notifications
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — Google OAuth
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` — GitHub OAuth

**Secrets:** `.env` file (not committed, user-provided)

*Integration audit: 2026-07-09*
