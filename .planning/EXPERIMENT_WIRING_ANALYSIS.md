# Experiment Wiring Analysis & Implementation Plan

**Last updated:** 2026-07-09  
**Status:** Analysis complete — trace, root causes, and dependency-ordered plan

---

## Executive Summary

The project has **three independent execution modes** (user-directed research, flexible research, idle autonomous), each with different wiring paths. The experiment pipeline branches after hypothesis formation:

```
Hypotheses → Validation Plan → Generate Experiment Code → Run in Sandbox → Validate → Report
```

**Critical finding:** The experiment wiring between `PLAN_VALIDATION` → `GENERATE_EXPERIMENT` → `RUN_EXPERIMENT` → `VALIDATE_HYPOTHESES` exists at the orchestration level but has **no automated end-to-end test coverage**, **multiple stub/fallback paths**, and **divergent validation plan engines** that don't share data structures.

**Total remaining work:** ~52 tasks across 6 dependency chains, estimated **8-12 weeks** for one full-time developer.

---

## Part 1: Full Experiment Wiring Trace

### 1.1 Frontend → API Entry Points

There are **three independent trigger paths**:

#### Path A: User-Directed Research (Main Path)
```
frontend: projects/[id]/page.tsx ("Start Run" button)
  → POST /api/v1/research/run
  → api/research.py: start_research_run()
  → Creates idea + run record in DB
  → background task: _run_workflow_background()
  → ResearchOrchestrator.run_research()
  → ResearchWorkflow.run() [17-step pipeline]
```

#### Path B: Idle Cycle
```
backend: idle_scheduler.py (cron-like background loop)
  → POST /api/v1/research/idle
  → api/research.py: start_idle_cycle()
  → ResearchOrchestrator.run_idle_cycle()
  → ResearchWorkflow._run_idle_autonomous() [4-step pipeline]
```

#### Path C: Direct Sandbox API
```
frontend: AnalysisToolsPanel (Plotly sandbox, power analysis)
  → POST /api/v1/sandbox/plotly
  → POST /api/v1/sandbox/power-analysis
  → api/sandbox_analysis.py
  → Direct SandboxExecutor.run_python() [no workflow steps]
```

### 1.2 Full 17-Step Workflow (Path A)

```
Step 1:  INTERPRET_INTENT    ← AgentRole.USER_INTENT (LLM)
Step 2:  PLAN_SEARCH         ← KeywordEngine (LLM + hardcoded expansion)
Step 3:  RETRIEVE_LITERATURE ← LiteratureEngine (8 connectors)
Step 4:  ANALYZE_PAPERS      ← AnalysisEngine (LLM)
Step 5:  CLUSTER_PAPERS      ← ClusteringEngine (LLM + algorithm)
Step 6:  DETECT_CONFLICTS    ← ConflictEngine (LLM + rule-based)
Step 7:  GENERATE_QUESTIONS  ← QuestionEngine (LLM)
Step 8:  FORM_HYPOTHESES     ← HypothesisEngine (LLM)
Step 9:  PLAN_VALIDATION     ← ValidationEngine (LLM + scoring)  ⚠️ SEE ISSUES
Step 10: SCORE_IDEA          ← ScoringEngine (LLM + heuristics)
Step 11: MAKE_DECISION       ← IdeaLedger (DB storage)
Step 12: GENERATE_EXPERIMENT ← AgentRole.DEVELOPER (LLM)  ⚠️ SEE ISSUES
Step 13: RUN_EXPERIMENT      ← SandboxExecutor (Docker)  ⚠️ SEE ISSUES
Step 14: VALIDATE_HYPOTHESES ← Heuristic + ClaimExtraction (LLM)  ⚠️ SEE ISSUES
Step 15: CREATE_SKILLS       ← DB insert (pattern abstraction)
Step 16: GENERATE_MANUSCRIPT ← ManuscriptService (LLM + LaTeX template)
Step 17: GENERATE_REPORT     ← AgentRole.ARCHIVIST (LLM)
```

### 1.3 The Experiment Sub-Chain (Steps 9→13→14)

This is the critical path that the gap analysis identified as broken:

```
PLAN_VALIDATION (Step 9)
  ├── Calls validation_engine.create_validation_plan()
  │   └── This creates ValidationPlan object WITH:
  │       ├── dataset_candidates (list[DatasetCandidate])
  │       ├── baselines (list[str])
  │       ├── metrics (list[str])
  │       ├── experimental_design (str — LLM-generated prose)
  │       └── statistical_tests (list[str])
  │
  └── Stores in state.validation_plans as dict (NOT the ValidationPlan object)
      └── Captures: feasibility_score, difficulty_estimate, cost_estimate
          └── This is used by SCORE_IDEA (Step 10) for scoring
              └── BUT the full plan (datasets, baselines, metrics, tests) IS LOST

GENERATE_EXPERIMENT (Step 12)
  ├── AgentRole.DEVELOPER (LLM) generates code from:
  │   ├── state.hypotheses (model_dump)
  │   └── state.current_idea
  │
  ├── Output: Python code extracted from ```python``` block
  │   └── FALLBACK: _fallback_experiment_code()
  │       └── Generates synthetic scaffold — no real validation logic
  │
  └── CRITICAL: Does NOT use validation plan data!
      ├── Does NOT pass dataset_candidates
      ├── Does NOT pass baselines/metrics/statistical_tests
      └── The LLM generates experiment code blind

RUN_EXPERIMENT (Step 13)
  ├── SandboxExecutor.run_python(code)
  │   ├── Volume-mounts script into Docker container
  │   ├── Runs with --read-only filesystem
  │   ├── Outputs to /app/outputs/ (writable volume) ✅ FIXED THIS SESSION
  │   └── Harvests artifacts ✅ FIXED THIS SESSION
  │
  ├── FALLBACK: _run_experiment_local() (dev mode only)
  │   └── Runs `python3 -c <code>` on host ⚠️ NOT DOCKERIZED
  │
  └── Result stored in state.experiment_result

VALIDATE_HYPOTHESES (Step 14)
  ├── Heuristic: success → "validated" (+0.15 confidence)
  │              failure → "rejected" (-0.20 confidence)
  │   └── No analysis of actual stdout/stderr content
  ├── Stage 2: ClaimExtraction (LLM)
  │   └── Extracts structured claims from experiment output
  └── Updates hypothesis status in DB
```

---

## Part 2: Root Cause Analysis of Failure Points

### 🔴 Failure Point 1: Validation Plan → Experiment Code Disconnect

**Severity:** CRITICAL  
**Root cause:** The `ValidationPlan` object created in Step 9 is serialized into `state.validation_plans` as a **partial dict** (only feasibility/difficulty/cost), then Step 12's `GENERATE_EXPERIMENT` never reads it. The LLM generates experiment code from hypothesis text alone — no datasets, baselines, or metrics provided.

**Evidence from code (workflow.py lines 967-999):**
```python
# Step 9 stores data as dict — discarding datasets, baselines, metrics
state.validation_plans.append({
    "hypothesis_id": plan.hypothesis_id,
    "hypothesis_statement": h.statement,
    "feasibility_score": plan.feasibility_score,   # ✅ kept
    "difficulty_estimate": plan.difficulty_estimate,
    "cost_estimate": plan.cost_estimate,
    # ❌ datasets, baselines, metrics, tests DISCARDED
})

# Step 12 generates code from hypothesis alone:
task = ("Generate a self-contained Python script to validate the primary hypothesis...")
input = AgentInput(
    task=task,
    context={
        "hypotheses": [h.model_dump() for h in state.hypotheses],
        "idea": state.current_idea,
        # ❌ NO validation plan data passed
    },
)
```

**Impact:** The experiment code generated by the LLM is generic and doesn't test specific hypotheses against specific datasets/metrics. Validation results are meaningless.

### 🔴 Failure Point 2: Dual Validation Plan Engines

**Severity:** HIGH  
**Root cause:** There are **two independent validation plan implementations**:

1. **`ValidationPlanningEngine`** (in `engine/validation_planning.py`) — Full-featured, uses LLM to design datasets, baselines, metrics, tests, cost/feasibility. Creates `ValidationPlan` dataclass objects.
2. **`ValidationPlanService`** (in `services/validation_service.py`) — DB persistence layer. Stores plans created by the engine.

The `ResearchWorkflow._plan_validation()` calls `self.validation_engine.create_validation_plan()` which uses engine #1. But the `generate_script` endpoint in `api/questions.py` fetches plans from the DB via `HypothesisService.get_validation_plan()`.

**But wait** — the workflow's validation engine call signature is:
```python
plan = await self.validation_engine.create_validation_plan(
    hypothesis={"statement": h.statement, "confidence": h.confidence},
    idea=state.current_idea,                         # ⚠️ different keyword
)
```

While the engine's actual method signature is:
```python
async def create_validation_plan(
    self,
    hypothesis: dict[str, Any],
    idea_context: str,                                # ⚠️ different parameter name
) -> ValidationPlan:
```

**Parameter mapping mismatch:** The workflow passes `idea=state.current_idea` but the engine expects `idea_context=`. Since Python matches by named parameter, `idea` would not match `idea_context` — this would likely cause a TypeError or silent fallback!

### 🟡 Failure Point 3: Sandbox Script Generator Replaced — API Not Updated

**Severity:** HIGH  
**Root cause:** The `sandbox_generator.py` generates Python scripts from `validation_plan` data. The `POST /hypotheses/{id}/generate-script` endpoint calls it. But the `ResearchWorkflow._generate_experiment()` (Step 12) uses the LLM agent instead of the sandbox generator.

**Two competing code generators:**
1. `sandbox_generator.py` — generates templates from validation plan data (datasets, baselines, metrics, tests) — FIXED THIS SESSION
2. `ResearchWorkflow._generate_experiment()` — uses LLM agent to create arbitrary code — NOT using sandbox generator

The sandbox generator was fixed this session (stub functions replaced with working implementations), but the workflow still doesn't use it.

### 🟡 Failure Point 4: Hypothesis Validation Is Heuristic

**Severity:** MEDIUM  
**Root cause:** `_validate_hypotheses()` only checks `result.success` (boolean). If the sandbox execution succeeds, all hypotheses are marked "validated" with a generic confidence boost. If it fails, all are marked "rejected." There is no analysis of whether the actual experiment results support or refute each hypothesis independently.

```python
# Step 14 (workflow.py lines 1205-1210):
if experiment_success:
    new_status = "validated"
    confidence_delta = 0.15
else:
    new_status = "rejected"
    confidence_delta = -0.20
```

The Stage 2 claim extraction partially addresses this by extracting structured claims from experiment output, but the claim results don't feed back into hypothesis status — they're stored in `state.claims` but never update hypothesis confidence individually.

### 🟡 Failure Point 5: No End-to-End Test Coverage

**Severity:** HIGH  
**Root cause:** The test directory `tests/` has no tests for `sandbox_generator.py`, `executor.py`, `sandbox_analysis.py`, or the experiment sub-chain (Steps 9→13→14). The only sandbox-related test infrastructure is Docker-dependent, making CI testing impractical.

### 🟢 Failure Point 6: DB Schema Stores Plans as JSON Strings

**Severity:** LOW  
**Root cause:** The `ValidationPlan` model stores `dataset_candidates` as a JSON column, `baselines` as JSON, `statistical_tests` as JSON, etc. While functionally correct, this means querying "all plans using dataset X" requires a full table scan.

---

## Part 3: Key Misalignments

| Misalignment | Layer | Impact | Fix |
|-------------|-------|--------|-----|
| Validation plan data discarded between Steps 9→12 | Backend data flow | Experiment code is hypothesis-blind | Pass full plan to code generator |
| `idea=` vs `idea_context=` parameter mismatch | Backend API | Step 9 may silently fail | Fix parameter name in `_plan_validation()` |
| Two independent code generators (LLM vs template) | Backend architecture | Divergent code quality | Consolidate: use sandbox_generator for structured validation, LLM for exploratory |
| Hypothesis validation is boolean-only | Backend logic | False positives/negatives | Implement per-result analysis |
| Workflow `_run_experiment()` doesn't pass validation plan | Backend orchestration | Sandbox code has no context | Inject validation plan into executor context |
| DB `validation_plans` schema is JSON-typed | Data model | Non-queryable | Add at least `hypothesis_id` FK index |
| No tests for experiment pipeline | Testing | Regression risk | Add unit + integration tests |

---

## Part 4: Remaining Tasks Organized by Dependency Chain

### Dependency Chain A: Fix the Experiment Pipeline Core (P0, 2 weeks)

**Pre-requisite:** Sandbox generator stubs fixed ✅, harvest_artifacts fixed ✅, frontend toasts fixed ✅

```
Chain A1: Fix validation plan passthrough
  ├── A1a. Fix parameter name: idea → idea_context in workflow._plan_validation
  ├── A1b. Store full ValidationPlan in state (not partial dict)
  ├── A1c. Pass validation plan to _generate_experiment as context
  └── A1d. Pass validation plan to SandboxExecutor.run_python() as metadata

Chain A2: Consolidate code generators
  ├── A2a. _generate_experiment should try sandbox_generator first, fall back to LLM
  ├── A2b. Add "generate from template" endpoint that uses fixed sandbox_generator
  └── A2c. Remove _fallback_experiment_code or upgrade to use load_data()

Chain A3: Improve hypothesis validation
  ├── A3a. Parse experiment stdout for per-hypothesis results
  ├── A3b. Feed claim extraction back into hypothesis status/confidence
  └── A3c. Add "inconclusive" status for experiments that ran but didn't test
```

### Dependency Chain B: Connector Resilience (P0, 1 week)

```
Chain B1: Backoff + retry
  ├── B1a. Implement exponential backoff with jitter in ConnectorManager._search_source
  ├── B1b. Distinguish retryable (429, 503) from non-retryable (400, 404) errors
  ├── B1c. Add max_total_wait and circuit-breaker state
  └── B1d. Propagate rate-limit headers to caller for backpressure
```

### Dependency Chain C: Bare except Exception Cleanup (P1, 2-3 weeks)

```
Chain C1: Services layer (largest batch)
  ├── C1a. orchestrator.py — 9 instances
  ├── C1b. research_persistence_service.py — 9 instances
  ├── C1c. report_generator.py — 4 instances
  ├── C1d. idle_scheduler.py — 5 instances
  ├── C1e. sse_stream.py — 4 instances
  ├── C1f. skill_evaluation_scheduler.py — 3 instances
  └── C1g. cache_service.py — 5 instances

Chain C2: API handlers
  ├── C2a. api/research.py — 3 instances
  ├── C2b. api/ideas.py — 3 instances
  ├── C2c. api/skills.py — 4 instances
  └── C2d. api/approvals.py, api/search.py, api/auth.py — 1 each

Chain C3: LLM providers
  ├── C3a. llm/router.py — 4 instances
  ├── C3b. llm/local_provider.py — 2 instances
  └── C3c. llm/llamacpp_provider.py — 2 instances

Chain C4: Remaining ~15 instances
  ├── event_stream.py, notification_service.py, manuscript_service.py
  ├── user_activity_service.py, evaluation.py, revision_workflow_service.py
  └── embedding_service.py, skill_performance_service.py
```

### Dependency Chain D: Testing (P1, 2-3 weeks)

**Depends on:** Chain A (must fix pipeline before testing it)

```
Chain D1: Experiment pipeline unit tests
  ├── D1a. Test sandbox_generator template generation
  ├── D1b. Test executor harvest_artifacts with mock directories
  ├── D1c. Test _fallback_experiment_code output
  └── D1d. Test workflow._run_experiment with mock executor

Chain D2: Integration tests
  ├── D2a. Test POST /hypotheses/{id}/generate-script
  ├── D2b. Test POST /sandbox/plotly with mock Docker
  └── D2c. Test POST /research/run → status polling

Chain D3: Frontend component tests
  ├── D3a. Test toast system (errorEvents.ts, GlobalErrorToast.tsx)
  ├── D3b. Test error display components
  └── D3c. Vitest setup for key page components
```

### Dependency Chain E: Operational Tools (P2, 1 week)

```
Chain E1: Health endpoint
  ├── E1a. Create GET /health aggregating DB, Redis, LLM providers, connectors
  ├── E1b. Add connector health to frontend dashboard
  └── E1c. Add periodic health check with alerting

Chain E2: Connector health dashboard
  ├── E2a. Frontend component showing per-connector status
  └── E2b. Auto-polling with visual indicator
```

### Dependency Chain F: Backlog Items (P3, 2-3 weeks)

```
Chain F1: Kaggle connector implementation
Chain F2: Consolidate embedding services (embedding_service vs knowledge_service)
Chain F3: Typed API response interfaces for all frontend endpoints
Chain F4: Overleaf sync (OAuth + API)
Chain F5: Collaboration mode (CRDT or operational transform)
Chain F6: JSON raw data export
Chain F7: Property-based / fuzz testing with hypothesis framework
```

---

## Part 5: Dependency Graph

```
Week 1      Week 2-3     Week 4-6      Week 7-8      Week 9-12
┌─────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌────────────┐
│ Chain B │→│ Chain A  │→│ Chain C   │→│ Chain E   │→│ Chain F    │
│ Retry   │ │ Pipeline │ │ except    │ │ Ops       │ │ Backlog    │
│ Backoff │ │ Fix      │ │ Cleanup   │ │           │ │            │
└─────────┘ └──────────┘ └───────────┘ └───────────┘ └────────────┘
                 ↓              ↓
              ┌──────────┐  ┌───────────┐
              │ Chain D  │  │           │
              │ Testing  │←─│ (parallel)│
              └──────────┘  └───────────┘
```

**Chain B** (connector retry) is the only independent chain — can start immediately.  
**Chain A** (pipeline fix) is the highest-impact but needs the sandbox generator fixes already done.  
**Chain D** (testing) depends on Chain A — don't write tests before fixing the pipeline.  
**Chain C** (except cleanup) and **Chain E** (ops) are independent of A and B.

---

## Part 6: Realistic Expectations

### What's Actually Working Today

| Feature | Status | Verified By |
|---------|--------|-------------|
| Literature search (8 connectors) | ✅ Working | Integration tests |
| Paper analysis + clustering | ✅ Working | Integration tests |
| Conflict detection | ✅ Working | Integration tests |
| Question + hypothesis generation | ✅ Working | Integration tests |
| Idea scoring + decision ledger | ✅ Working | Integration tests |
| Sandbox executor (Docker) | ✅ Working (partially) | Manual testing |
| Sandbox generator template | ✅ Fixed this session | Code review |
| Sandbox artifact harvesting | ✅ Fixed this session | Code review |
| Frontend toast on API errors | ✅ Fixed this session | Code review |
| Manuscript generation (LaTeX) | ✅ Working | Integration tests |
| Citation + export pipeline | ✅ Working | Integration tests |

### What's Broken or Missing

| Feature | Status | Root Cause |
|---------|--------|------------|
| Experiment pipeline (Steps 9→12→13→14) | ❌ Broken | FP1-4 (validation plan disconnect, dual engines, parameter mismatch, heuristic validation) |
| Connector retry with backoff | ❌ Missing | No implementation |
| `except Exception` across 50+ files | ❌ Still broken | ~77 instances remain (connectors fixed) |
| Frontend test coverage | ❌ Missing | 1 test file out of 40+ components |
| End-to-end experiment tests | ❌ Missing | No test infra for Docker-dependent code |
| System health endpoint | ❌ Missing | No `/health` aggregate endpoint |
| Kaggle connector | ❌ Stubbed | No implementation |

### Realistic Timeline

| Timeline | Deliverable | Confidence |
|----------|-------------|------------|
| **1 week** | Chain B: Connector retry with backoff | High — well-scoped, single file |
| **2 weeks** | Chain A: Experiment pipeline fix | Medium — requires careful data flow changes |
| **2-3 weeks** | Chain C: except Exception cleanup | Low — 50+ files, risk of introducing new bugs |
| **2-3 weeks** | Chain D: Test coverage | Medium — depends on Chain A completion |
| **1 week** | Chain E: Health endpoint + dashboard | High — well-scoped |
| **2-3 weeks** | Chain F: Backlog items | Low — scope varies |

**Total: 8-12 weeks** for one full-time developer working on these tasks exclusively.

### Ways to Improve Accuracy

1. **Instrument the experiment pipeline before fixing**: Add structured logging to Steps 9→12→13→14 with unique trace IDs. This makes root cause validation data-driven rather than code-read-driven.

2. **Add a sandbox integration test harness**: Create a test helper that mocks Docker subprocess calls using `unittest.mock.patch` for `asyncio.create_subprocess_exec`. This removes the Docker dependency from unit tests while still testing the code path.

3. **Validate parameter passing with a mypy/pyright strictness pass**: The `idea` vs `idea_context` mismatch was found by reading code — a strict type checker would have caught it. Add `# type: ignore` only where truly needed.

4. **Run the workflow with a dry-run flag**: Add a `dry_run=True` mode to `ResearchWorkflow._run_experiment` that logs what would happen without actually executing. This makes the pipeline testable without Docker.

5. **Create per-method unit tests for `_validate_hypotheses`**: The heuristic validation logic is the simplest part to test — no Docker, no LLM, just string comparison on experiment_result dict. Start here to build testing momentum.

6. **Trace the actual runtime behavior**: Set `LOG_LEVEL=DEBUG`, run a research workflow with a well-known hypothesis (e.g., "increasing training data improves model accuracy"), and capture the full event stream. This will reveal whether`_plan_validation` actually succeeds or silently fails due to the parameter mismatch.
