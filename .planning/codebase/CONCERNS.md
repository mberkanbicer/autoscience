# Codebase Concerns

**Analysis Date:** 2026-07-09

## Previously Documented Concerns (Now Resolved)

### ✅ Direct Database Writes in Orchestrator — RESOLVED

**Original issue:** `ResearchOrchestrator._store_results()` wrote directly to DB models instead of using service layer.
**Resolution:** `ResearchPersistenceService` was introduced to handle batch deduplication and paper persistence, refactoring the direct model writes from the orchestrator.
**Files:** `backend/app/services/research_persistence_service.py`, `backend/app/services/orchestrator.py`

### ✅ Lazy Import in Workflow — RESOLVED

**Original issue:** `KnowledgeBaseService` was lazily imported inside `_generate_wiki_notes()` to avoid circular imports.
**Resolution:** The import pattern is stable and well-tested. While technically still a lazy import, the pattern has proven reliable and the circular dependency is better understood.

### ✅ Sandbox Executor Placeholder — RESOLVED

**Original issue:** Sandbox executor returned hardcoded success message, no actual code execution.
**Resolution:** Full Docker sandbox implemented with Python script generation, safe execution with resource limits, artifact capture, Plotly visualization, and Jupyter notebook export.
**Files:** `backend/app/sandbox/executor.py`, `backend/app/sandbox/__init__.py`, `backend/app/engine/sandbox_generator.py`

### ✅ Workflow Step History Not Persisted — RESOLVED

**Original issue:** Step history resets on workflow restart; only exists in memory.
**Resolution:** Step history is now persisted and restored on workflow resume via `ResearchPersistenceService`.
**Files:** `backend/app/services/research_persistence_service.py`

### ✅ Frontend Test Coverage — RESOLVED

**Original issue:** No frontend tests configured.
**Resolution:** vitest configured (`frontend/vitest.config.ts`) with type tests for `settingsVault`. Playwright E2E test (`frontend/e2e/smoke.spec.ts`) for critical paths.

### ✅ CI Pipeline — RESOLVED

**Original issue:** No CI pipeline configured.
**Resolution:** GitHub Actions workflow at `.github/workflows/ci.yml`.

### ❌ N+1 Query Pattern in _store_results — PARTIALLY RESOLVED

**Original issue:** Paper deduplication queries all existing titles for a project (O(N)).
**Current state:** Partially addressed by `ResearchPersistenceService` batch operations. Still room for optimization at scale (>1000 papers).

---

## Current Concerns

### Module-Level Global State in Scheduler

**Issue:** `skill_evaluation_scheduler.py` uses module-level globals (`_scheduler_task`, `_runtime_config`, etc.) for scheduler state management.
**Files:** `backend/app/services/skill_evaluation_scheduler.py`
**Impact:** Works correctly in single-process uvicorn but would break under multi-worker or multi-process deployments.
**Current mitigation:** Single-process uvicorn is the deployment model. Module-level state is reset on each worker start.

### SSE Endpoint Requires Redis

**Issue:** The `/skills/performance/eval-stream` and `/search/stream/{run_id}` SSE endpoints require Redis for pub/sub message delivery.
**Files:** `backend/app/api/skills.py`, `backend/app/api/search.py`
**Impact:** Without Redis, SSE endpoints return client-side connection errors. The scheduler still works (logs to DB) but no real-time toast notifications.
**Current mitigation:** Redis connection failures are silently caught — the system degrades gracefully.

### Auth Dual-Path Pattern

**Issue:** Authentication supports both JWT Bearer tokens and header-based (`X-User-Email`, `X-User-Name`) fallback for local/dev.
**Files:** `backend/app/dependencies/auth.py`
**Impact:** The fallback path bypasses proper authentication. In production, the fallback headers should be disabled.
**Current mitigation:** Used only in local dev. Production deployments should configure proper OAuth/JWT.

### pgvector Not Centralized

**Issue:** pgvector embeddings used in multiple places (wiki sematic search, paper embeddings) but not managed through a centralized embedding service.
**Files:** `backend/app/services/embedding_service.py`, `backend/app/services/wiki_embedding_service.py`
**Impact:** Duplicated embedding logic, inconsistent vector dimensions.
**Recommendation:** Consolidate embedding operations under a single vector service.

---

## Security Considerations

### API Key Storage

**Risk:** Connector API keys (CORE, Firecrawl, Semantic Scholar) stored in environment variables.
**Current mitigation:** Environment variables only (never logged). Frontend has an encrypted API key vault (AES-GCM + PBKDF2) in Settings.
**Files:** `frontend/src/lib/settingsVault.ts`

### Sandbox Execution

**Risk:** Docker sandbox executes arbitrary Python code from validation plans.
**Current mitigation:** Docker containerization with resource limits (CPU, memory, timeout). Code is generated only from validated plans.
**Files:** `backend/app/sandbox/executor.py`

---

## Performance Considerations

### Redis Cache Invalidation

**Issue:** No systematic cache invalidation strategy. Cache entries may serve stale data.
**Files:** `backend/app/services/cache_service.py`
**Recommendation:** Add TTL-based expiry or event-driven cache invalidation.

### Asyncio Background Tasks

**Issue:** Background tasks (scheduler, idle scheduler) run inside the uvicorn event loop. Long-running tasks can block the loop.
**Files:** `backend/app/services/skill_evaluation_scheduler.py`, `backend/app/services/idle_scheduler.py`
**Current mitigation:** Tasks are pure async with `asyncio.sleep()` yielding control between cycles. No CPU-heavy work in the task.

---

## Test Coverage Gaps

### Full Workflow Integration Test

**What's not tested:** Complete end-to-end research workflow from API call through all 17 steps to report generation.
**Risk:** Integration bugs between orchestrator, workflow, engines, and services.
**Current tests:** Component-level tests exist for individual services and engines.

### SSE Endpoint Tests

**SSE endpoints** (`/skills/performance/eval-stream`, `/search/stream/{run_id}`) are not covered by tests since they require Redis.

---

*Concerns audit: 2026-07-09*
