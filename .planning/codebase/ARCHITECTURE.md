<!-- refreshed: 2026-07-09 -->
# Architecture

**Analysis Date:** 2026-07-09

## System Overview

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                                Frontend (Next.js React)                              │
│   [src/app] [src/components/ui/] [src/components/layout/] [src/hooks] [src/lib]      │
└─────────────────────────────────┬──────────────────────────────────────────────────┘
                                  │
                                  │ HTTP API (JSON) + SSE (text/event-stream)
                                  ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                            FastAPI Application (asyncio)                             │
│  [api/] [services/] [engine/] [agents/] [workflows/] [connectors/] [llm/] [sandbox/] │
└─────────────────────────────────┬──────────────────────────────────────────────────┘
                                  │
          ┌─────────────────────────┼──────────────────────────┐
          ▼                        ▼                          ▼
┌──────────────────┐    ┌─────────────────────┐    ┌─────────────────────────┐
│ Academic APIs    │    │  LLM Providers      │    │  PostgreSQL + Redis      │
│ arxiv, openalex, │    │  openai/anthropic/  │    │  Async SQLAlchemy 2.0    │
│ semantic scholar │    │  openrouter/local/  │    │  Alembic migrations      │
│ crossref, pubmed,│    │  llamacpp           │    │  pgvector embeddings     │
│ doaj, core,      │    │                     │    │                          │
│ unpaywall        │    │                     │    │  + External OAuth        │
│ + searxng,       │    │                     │    │  (Google, GitHub)        │
│ firecrawl (opt)  │    │                     │    │  + SMTP (optional)       │
└──────────────────┘    └─────────────────────┘    └─────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| ResearchOrchestrator | Coordinates all services and engines for research runs | `backend/app/services/orchestrator.py` |
| ResearchWorkflow | Durable 17-step workflow engine | `backend/app/workflows/research_workflow.py` |
| SkillEvalScheduler | Background asyncio loop for periodic skill evaluation | `backend/app/services/skill_evaluation_scheduler.py` |
| SkillPerformanceService | Evaluates skills against thresholds, auto-deprecates/retires | `backend/app/services/skill_performance_service.py` |
| EventBroadcaster | Redis pub/sub for SSE event streaming | `backend/app/services/event_stream.py` |
| SafetyService | Spend thresholds, approval gates, safety policy | `backend/app/services/safety_service.py` |
| RevisionWorkflowService | Manuscript revision cycle | `backend/app/services/revision_workflow_service.py` |
| AuthService | JWT + header auth, OAuth (Google/GitHub) | `backend/app/services/auth_service.py` |
| ConnectorManager | Manages all academic source connectors | `backend/app/connectors/manager.py` |
| CacheService | Redis-based caching for API responses | `backend/app/services/cache_service.py` |
| ManuscriptGenerator | IMRaD manuscript generation with citations | `backend/app/engine/manuscript_engine.py` |
| SandboxExecutor | Docker sandbox for running experiment scripts | `backend/app/sandbox/executor.py` |

## Layers

**Frontend (Next.js 14):**
- Purpose: React SPA with TypeScript, Tailwind CSS, App Router
- Location: `frontend/src/`
- Contains: Pages (`app/`), UI components (`components/ui/`), layout (`components/layout/`), hooks (`hooks/`), API client (`lib/api.ts`), types (`lib/types.ts`)
- Key pages: projects, ideas, papers, clusters, questions, hypotheses, reports, wiki, skills, manuscripts, datasets, approval, settings, studio, pipeline, health, team, article-studio

**API Layer (FastAPI):**
- Purpose: REST endpoints for all CRUD and research control
- Location: `backend/app/api/`
- 20 routers: projects, ideas, runs, papers, skills, questions, hypotheses, reports, wiki, manuscripts, research, search, datasets, approvals, auth, collaboration, connectors, sandbox, user_activity, organizations
- Main router: `backend/app/api/router.py`
- All endpoints prefixed with `/api/v1/`

**Service Layer:**
- Purpose: Business logic, state management, orchestration
- Location: `backend/app/services/` (48 files)
- Key services: orchestrator, knowledge_service, skill_performance_service, skill_evaluation_scheduler, revision_workflow_service, auth_service, oauth_service, safety_service, event_stream, sse_stream, notification_service, report_generator, snapshot_service, research_persistence_service, manuscript_service, latex_compiler, peer_review_service, artifact_linking_service, dataset_upload_service, embedding_service, wiki_graph_service, notebook_export_service

**Engine Layer:**
- Purpose: Core cognitive operations (LLM-powered)
- Location: `backend/app/engine/` (21 files)
- Engines: keyword_engine, literature_engine, paper_analysis, clustering, conflict_detection, question_generation, hypothesis_generation, validation_planning, scoring, deduplication, idle_cognition, manuscript_engine, claims_pipeline, effect_size_extraction, sandbox_generator, power_analysis, domain_packs, journal_templates, latex_numbering

**Agent Layer:**
- Purpose: Specialized LLM agents with distinct personas
- Location: `backend/app/agents/`
- Roles: Orchestrator, UserIntent, Literature, PaperAnalyst, Cluster, Conflict, ResearchQuestion, Hypothesis, ValidationPlanner, DataAnalyst, Skeptic, Decision, SkillCurator, Archivist, Developer, ScientificWriter
- Config: `backend/app/agents/base.py`

**Model Layer:**
- Purpose: SQLAlchemy async models
- Location: `backend/app/models/` (11 model files)
- Models: Project, Idea + IdeaVersion/IdeaScore/IdeaClassification/IdeaDecision, ResearchRun + ResearchRunEvent/ToolCall/IdleCycle, Paper + PaperSource/PaperFulltext/PaperEmbedding/PaperAnalysis, PaperCluster + ClusterLabel/ClusterConflict, ResearchQuestion + Hypothesis/ValidationPlan, Skill + SkillVersion/SkillUsage/SkillEvaluation, Report + KnowledgeNote/LiteratureSearch/SearchQuery/Dataset/AnalysisRun/AnalysisArtifact, AuditLog + ApprovalRequest/SystemEvent, Collaboration (User/ProjectMember/Comment/ReviewProposal), Organization

**Connector Layer:**
- Purpose: External academic API integrations
- Location: `backend/app/connectors/` (16 files)
- Connectors: ArxivConnector, SemanticScholarConnector, OpenAlexConnector, CrossrefConnector, PubMedConnector, DOAJConnector, COREConnector, UnpaywallConnector, SearXNGConnector (optional), FirecrawlConnector (optional)
- Serialization helpers in `serialization.py`
- Dataset connectors: `dataset_connectors.py` (HuggingFace, Zenodo, Kaggle)

**LLM Layer:**
- Purpose: Pluggable LLM providers
- Location: `backend/app/llm/`
- Providers: OpenAI, Anthropic, OpenRouter, Local (Ollama), Llama.cpp
- Router: `router.py` with failover support

## Data Flows

### Primary Research Run

1. Frontend initiates via `researchApi.start()` → `POST /api/v1/research/run`
2. API creates ResearchOrchestrator → calls `run_research()`
3. Orchestrator creates ResearchWorkflow → executes 17 steps
4. Each step delegates to appropriate engine/agent
5. Results stored in DB via orchestrator `_store_results()` (batch deduplication via ResearchPersistenceService)
6. SSE events broadcast via EventBroadcaster (Redis pub/sub)
7. Report generated, knowledge base updated, skills extracted
8. Frontend receives state via API + SSE stream

### Idle Cognition

1. IdleScheduler checks idle projects every N minutes
2. Locks project via Redis or DB lock
3. Triggers IdleCognitionEngine → generates ideas, questions, skills autonomously
4. Results stored, audit logged, scheduler loop continues

### Skill Evaluation

1. Background asyncio task runs on configurable interval (1h–72h)
2. SkillPerformanceService evaluates all skills against thresholds (30% success rate, negative score impact)
3. Auto-deprecates/retires low-performing skills with grace period (30 days)
4. Results logged to audit database and broadcast via SSE
5. Frontend receives real-time toast notifications via `useSkillEvalStream` hook

## Key Architectural Decisions

- **Async-first**: All database operations use AsyncSession, HTTP clients are async
- **Module-level globals**: Scheduler state stored at module level (single-process uvicorn)
- **Lazy imports**: Used in workflow to avoid circular imports (knowledge service, etc.)
- **Pydantic v2**: All schemas use `model_dump()` / `model_validate()` (no deprecated v1 methods)
- **Structlog**: Structured JSON logging across all services
- **RBAC**: Project roles enforced on all sensitive endpoints (viewer/editor/admin)
- **JWT auth**: Bearer token with header-based fallback for local/dev

*Architecture analysis: 2026-07-09*
