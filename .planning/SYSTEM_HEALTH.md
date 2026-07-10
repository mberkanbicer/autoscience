# System Health & Technical Debt Tracking

**Last updated:** 2026-07-09  
**Status phase:** v2.6 Polish & Gap Closure  
**Audit method:** Automated code-searcher analysis + manual review of 9 connector files, 20+ page/component files, sandbox, and orchestration layers

---

## Priority Legend

| Priority | Definition | Action |
|----------|-----------|--------|
| **P0** | Bug-level risk — silent data loss, crashes, or incorrect results | Fix immediately |
| **P1** | Operational risk — degrades UX, hides failures, blocks pipeline | Fix this milestone |
| **P2** | Quality risk — technical debt, missing visibility, untested paths | Schedule next milestone |
| **P3** | Hygiene — nice-to-have improvements, cleanup | Backlog |

---

## ✅ Recently Completed (v2.6 Session)

| Item | Priority | Files Changed | Summary |
|------|----------|---------------|---------|
| Replace bare `except Exception` in 8 academic connectors | P0 | 8 connector files + `base.py` | All 26+ blocks replaced with `httpx.HTTPStatusError`, `httpx.TimeoutException`, `httpx.RequestError`, `json.JSONDecodeError`, `ET.ParseError`, and `(KeyError, ValueError, TypeError[, AttributeError])` |
| Skill evaluation SSE broadcast | v2.6 | `api/skills.py`, frontend hook | Real-time toast notifications via EventSource |
| Scheduler settings UI | v2.6 | `SkillEvalSettings.tsx`, `api/skills.py` | Enable/disable, interval selector, dry run, Run Now |
| Evaluation history panel | v2.6 | `SkillEvalHistory.tsx`, `api/skills.py`, `types.ts` | Audit-log-backed event list with expandable details |
| `.planning/` docs update | v2.6 | 12 planning files | All codebase docs rewritten to reflect v2.0–v2.6 |

---

## 🔴 P0 — Fix Immediately

### 1. Sandbox Script Generator Has Stub Methods
**File:** `backend/app/engine/sandbox_generator.py`

**Status:** ✅ Completed 2026-07-09

**What was done:**
- `hypothesis_metric()` now computes descriptive statistics (mean, std, min, max, count, missing%) per numeric column
- `evaluate_baseline()` now computes per-column means, stds, medians, Q1/Q3, and class balance — replaces the undefined `baseline_metric()` call
- `statistical_test()` now uses scipy.stats (t-test, KS-test, Shapiro-Wilk) with Cohen's d effect size, with numpy-descriptive fallback when scipy unavailable
- `load_data()` now generates synthetic control/treatment data when no datasets found
- Output path changed to `/app/outputs/validation_results.json` (matching the new writable Docker volume)

### 2. Sandbox Artifact Harvesting Is Empty
**File:** `backend/app/sandbox/executor.py`

**Status:** ✅ Completed 2026-07-09

**What was done:**
- `harvest_artifacts()` now scans the output directory for JSON, CSV, TSV, PNG, SVG, PDF, TXT, HTML, NPY, NPZ files
- JSON files parsed and included as dicts; text/CSV as raw strings; images/PDF as base64 data URIs; numpy arrays as metadata
- 50MB size cap with warning log for oversized files
- Symlink check prevents directory traversal from container
- Files manifest (`files`) and parsed content (`data`) returned together
- Results automatically attached to `SandboxResult.artifacts` after each `run_python()` call
- Added writable `/app/outputs` Docker volume mount so generated scripts can write results

### 3. Retry With Backoff in Connectors
**File:** `backend/app/connectors/manager.py`

`_search_source` has a naive 2-attempt retry with a hardcoded 0.5s sleep:
```python
for attempt in range(2):
    try:
        result = await connector.search(query)
        return source_name, result
    except Exception as exc:
        if attempt == 0:
            await asyncio.sleep(0.5)
            continue
```

**Issues:**
- No exponential backoff — retries hammer failing APIs at the same rate
- No distinction between retryable (429 rate-limit, 503 temporary) and non-retryable (400 bad request, 404 not found) errors
- No jitter — synchronized retries across parallel connector searches
- No max total wait time or circuit breaker

**Impact:** High — API rate limits trigger cascading failures across all connectors.

**Effort:** Medium  
**Owner:** —  
**Status:** ⬜ Not started

### 4. Bare `except Exception` in Services, API Handlers, LLM Router
**Count:** 77 remaining instances outside connectors

| Area | Instances | Risk |
|------|-----------|------|
| `orchestrator.py` | 9 | Catches all errors, masks orchestration failures |
| `research_persistence_service.py` | 9 | Silently swallows DB errors |
| `report_generator.py` | 4 | LLM report generation errors hidden |
| `idle_scheduler.py` | 5 | Background task failures masked |
| `sse_stream.py` | 4 | Event stream disconnection errors caught broadly |
| `skill_evaluation_scheduler.py` | 3 | Scheduler failures masked |
| `api/research.py` | 3 | API handler errors caught broadly |
| `api/ideas.py` | 3 | Idea ledger failures masked |
| `cache_service.py` | 5 | Cache failures silently degrade |
| Other | ~30 | Spread across `llm/router.py`, `event_stream.py`, `auth.py`, `approvals.py`, `embedding_service.py`, etc. |

**Impact:** High — systemic issue masking real failures. `KeyboardInterrupt` and `asyncio.CancelledError` are silently caught.

**Note:** Connectors (26 instances) were already fixed in this session.

**Effort:** Large (~50 files)  
**Owner:** —  
**Status:** 🔄 In progress (connectors done)

---

## 🟡 P1 — Fix This Milestone

### 1. Frontend Error Handling Is `console.error` Only
**Count:** 72 instances across 20+ page/component files

**Status:** ✅ Completed 2026-07-09

**What was done:**
- Created `frontend/src/lib/errorEvents.ts` — module-level event emitter (no React dependency)
- Modified `api.ts` `request()` — now calls `emitApiError()` before throwing on every failed response, including `error.detail` fallback for FastAPI's `{"detail": "..."}` error format
- Created `frontend/src/components/GlobalErrorToast.tsx` — subscribes to error events, maps status codes to human-readable titles (404→"Resource not found", 429→"Rate limited", 500+→"Server error"), shows 6s error toast with capped message
- Wired into `providers.tsx` inside `ToastProvider`

**Result:** Every failing API call now auto-shows a user-facing toast. The 72 existing `console.error` calls remain for debugging. No page-level modifications needed — the toast fires from the shared `request()` function.

### 2. No User-Facing Notification Toast System
**Related to:** P1 frontend error handling

The `ErrorBoundary` component exists but shows a generic fallback. No toast/snackbar system exists for transient errors. Users have no way to know an API call failed unless they check the browser console.

**Impact:** Medium — degrades UX significantly. Users can't distinguish "loading" from "failed silently."

**Effort:** Small (create `<Toast />` component + context provider)  
**Owner:** —  
**Status:** ⬜ Not started

### 3. Embedding Service Has Two Competing Implementations
**Files:**
- `backend/app/services/embedding_service.py`
- `backend/app/services/knowledge_service.py` (has its own embedding methods)

Both use different approaches (caching, batching, provider selection). No shared interface or configuration.

**Impact:** Low–Medium — duplication leads to drift. When one gets rate-limit handling, the other doesn't.

**Effort:** Medium (extract common interface, consolidate)  
**Owner:** —  
**Status:** ⬜ Not started

### 4. No System Health Endpoint
**Current state:** No `/health` endpoint exists that checks DB connectivity, Redis, LLM providers, sandbox, and connectors together. Individual `health_check` methods exist on connectors but aren't aggregated into a dashboard.

**Impact:** Medium — operational visibility gap. Can't monitor system health programmatically.

**Effort:** Small (add aggregated health endpoint + optional dashboard integration)  
**Owner:** —  
**Status:** ⬜ Not started

---

## 🟠 P2 — Next Milestone

### 1. Frontend Unit Tests
**Current state:** Only one vitest test exists (`settingsVault.test.ts`). The Playwright E2E smoke test covers only basic page load.

**Missing:**
- Component-level unit tests for all UI components
- Hook tests for custom hooks (`useSkillEvalStream`, `useActivityHeartbeat`, etc.)
- Integration tests for API-layer interactions
- Regression tests for critical user flows

**Impact:** Medium — UI regressions are undetected. Refactoring frontend code is risky.

**Effort:** Medium (create test patterns, then expand coverage incrementally)  
**Owner:** —  
**Status:** ⬜ Not started

### 2. Connector Health Dashboard Integration
**Status:** Connectors have individual `health_check()` methods and `ConnectorManager` has `health_check()`. But:
- No frontend component consumes this data
- No periodic check
- No backpressure mechanism when a connector is down

**Impact:** Low — informational, but useful for debugging integration issues.

**Effort:** Small  
**Owner:** —  
**Status:** ⬜ Not started

### 3. No Property-Based or Fuzz Testing
**Current state:** Only `test_openapi_contract.py` runs in CI for API validation. No property-based or fuzz testing exists.

**Impact:** Low — the contract test catches basic shape mismatches but not edge cases.

**Effort:** Medium (add hypothesis framework, write property tests for key services)  
**Owner:** —  
**Status:** ⬜ Not started

---

## 🔵 P3 — Backlog

| Item | Effort | Impact | Notes |
|------|--------|--------|-------|
| **Kaggle connector implementation** | Small | Low | `dataset_connectors.py` has a stubbed `KaggleConnector` |
| **Consolidate embedding services** | Medium | Low | Two competing implementations with no shared interface |
| **Typed API response interfaces (frontend)** | Large | Medium | Many API responses use `JsonRecord` / `any` instead of typed interfaces |
| **Overleaf sync** | Medium | Low | OAuth + Overleaf API integration |
| **Collaboration mode (real-time editing)** | Large | Medium | Would require CRDT or operational transform |
| **JSON raw data export** | Trivial | Low | Small addition to existing export endpoints |

---

## Summary

| Priority | Total Items | Completed This Session | Remaining |
|----------|-------------|----------------------|-----------|
| P0 | 4 | 1 (connector `except Exception`) | 3 |
| P1 | 4 | 0 | 4 |
| P2 | 3 | 0 | 3 |
| P3 | 6 | 0 | 6 |
| **Total** | **17** | **1** | **16** |

---

## How to Use This Document

1. Before starting a new milestone, pick all items from P0, then as many P1 items as feasible
2. Mark items as `🔄 In progress` when work begins
3. Move to `✅ Completed` with a date when the fix is merged
4. Re-audit quarterly to catch new technical debt
