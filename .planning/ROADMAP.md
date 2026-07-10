# Roadmap: Deep Academic Research, Experiment, and Article Studio

## Milestone: Research Studio Foundation (v2.0) — COMPLETE

All v2.0 phases (0–9) and post-v2.0 polish items are implemented.

| Area | Status |
|------|--------|
| Research workflow (17 steps, sandbox, safety gates) | Done |
| Observability (`/search/stream`) | Done |
| Article Studio (LaTeX, tex/bib/zip/pdf, live preview) | Done |
| Datasets (HF/Zenodo/Kaggle, preview, export) | Done |
| Wiki (text + semantic embedding search) | Done |
| Paper comparison + citation graph | Done |
| CI/E2E (GitHub Actions, Vitest) | Done |
| pgvector verify script | Done |

---

## Milestone: v2.1 — Production Hardening — COMPLETE

### Phase 10.1: CI & Quality Gates — Done
### Phase 10.2: Sandbox & Connector Hardening — Done
### Phase 10.3: Wiki & Search Intelligence — Done

---

## Milestone: v2.2 — Collaboration — COMPLETE

### Phase 11.1: Multi-User Projects — Done
### Phase 11.2: Review Workflows — Done (MVP)
- Review assignee notifications (`/collaboration/notifications`)
- Activity feed includes `review_assigned` events

### Phase 11.3: OAuth — Done (MVP)
- Google/GitHub OAuth (`/auth/oauth/*`)
- Frontend callback page + Team page OAuth buttons

### Phase 11.4: RBAC Expansion — Done
- Skills APIs require project role
- Runs/research require editor

---

## Milestone: v2.3 — Publication Pipeline — COMPLETE

### Phase 12.1: Journal Templates — Done
### Phase 12.2: Preprint Integration — Done
### Phase 12.3: E2E & Contract Tests — Done

### Phase 12.4: Export Enhancements — Done (MVP)
- Figure/table auto-numbering in LaTeX exports
- Server-side LaTeX → PDF compile (pdflatex when available)

---

## Milestone: v2.4 — Domain Specialization — COMPLETE (MVP)

### Phase 13.1: Domain Packs — Done
### Phase 13.2: Peer Review Simulation — Done
### Phase 13.3: Analysis Sandbox Extensions — Done (MVP)
- Jupyter notebook export (`GET /runs/{id}/notebook`)
- Statistical power analysis (`POST /sandbox/power-analysis`)
- Plotly visualization sandbox (`POST /sandbox/plotly`)
- Wiki cross-run knowledge graph (`GET /wiki/graph`)

---

## Milestone: v2.5 — Polish & Hardening — COMPLETE

### Phase 14.1: Nice-to-Have UX — Done
- Expanded Playwright E2E (wiki, studio, settings, power API, shortcuts)
- Redis cluster support for idle scheduler locks (`REDIS_CLUSTER_NODES`)
- Mobile-responsive artifact panel (full-screen on small viewports)
- Keyboard shortcut overlay (`Shift+?`, `Esc`, `G P` / `G S`)

### Phase 14.2: MVP Hardening — Done
- RBAC on reports, questions, hypotheses, approvals
- Analysis tools UI (power, Plotly, notebook download) in Article Studio
- Connector health exposes optional registration status

### Phase 14.3: Concerns Addressed — Done
- Orchestrator uses `ResearchPersistenceService` (batch deduplication)
- Step history persisted and restored on workflow resume
- Pydantic v2 `model_dump` in persistence helpers

### Phase 14.4: Final Polish — Done
- Mobile sidebar drawer + top bar navigation
- Encrypted API key vault (AES-GCM + PBKDF2) in Settings
- Email notifications for review assignments (optional SMTP)
- In-app notification bell with toast alerts + read tracking
- Responsive headers and layout spacing

---

## Milestone: v2.6 — Skill Evaluation & Scheduler Control — COMPLETE

### Phase 15.1: Real-Time Evaluation Notifications — Done
- Skill evaluation event broadcasting via SSE (Redis pub/sub channel)
- SSE endpoint for system evaluation events (`/skills/performance/eval-stream`)
- Frontend `useSkillEvalStream` hook with deduplication and exponential backoff reconnect

### Phase 15.2: Scheduler Settings UI — Done
- Runtime scheduler configuration API (GET/PATCH `/skills/performance/scheduler-config`)
- Scheduler status endpoint with live run count and last-run timestamp
- Master toggle (immediate start/stop), interval selector (1h–72h, staged), dry run mode toggle
- Manual "Run Now" button with SSE broadcast integration

### Phase 15.3: Evaluation History Panel — Done
- `GET /skills/performance/eval-history` endpoint querying audit log
- Color-coded event list (green=ok, amber=changes, red=errors)
- Click-to-expand detail view with raw field inspection
- Empty state, loading skeleton, error retry

---

## Future Backlog (no milestone assigned)

| Item | Impact | Effort | Notes |
|------|--------|--------|-------|
| Overleaf sync | Low | Medium | OAuth + Overleaf API integration |
| Collaboration mode (real-time editing) | Medium | Large | CRDT or operational transform |
| JSON raw data export | Low | Trivial | Small addition to existing export endpoints |

---
*Roadmap updated: 2026-07-09*