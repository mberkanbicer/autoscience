# Roadmap

> **Status note:** This roadmap records the original 32-phase build plan. The
> system has since been implemented end-to-end (backend, frontend, CI, and a
> comprehensive test suite). Treat the phase table below as historical context
> rather than a live status board.

## Overview

This document outlines the development phases for the Background Scientific Cognition System. The project is built in 32 sequential phases, each producing a verifiable layer of the final architecture.

**Approach:** Complete system, not MVP. Correctness over speed. Every phase verified before moving to the next.

**Solo developer. Open-ended timeline.**

---

## Phase Summary

| # | Phase | Status |
|---|---|---|
| 1 | Repository & Documentation | 🔄 In Progress |
| 2 | Backend Foundation | ⬜ Pending |
| 3 | Complete Data Model | ⬜ Pending |
| 4 | Research State & Audit | ⬜ Pending |
| 5 | LLM Provider Abstraction | ⬜ Pending |
| 6 | Academic Connectors | ⬜ Pending |
| 7 | Keyword Expansion | ⬜ Pending |
| 8 | Literature Retrieval | ⬜ Pending |
| 9 | Paper Analysis | ⬜ Pending |
| 10 | Clustering | ⬜ Pending |
| 11 | Conflict Detection | ⬜ Pending |
| 12 | Question Generation | ⬜ Pending |
| 13 | Hypothesis Generation | ⬜ Pending |
| 14 | Validation Planning | ⬜ Pending |
| 15 | Idea Scoring | ⬜ Pending |
| 16 | Idea Ledger | ⬜ Pending |
| 17 | Skill Memory | ⬜ Pending |
| 18 | Idle Cognition | ⬜ Pending |
| 19 | Agent Definitions | ⬜ Pending |
| 20 | Workflow Engine | ⬜ Pending |
| 21 | Data Analysis Sandbox | ⬜ Pending |
| 22 | Knowledge Base | ⬜ Pending |
| 23 | Reporting | ⬜ Pending |
| 24 | Approval & Safety | ⬜ Pending |
| 25 | Frontend Setup | ⬜ Pending |
| 26 | Frontend Projects | ⬜ Pending |
| 27 | Frontend Ideas | ⬜ Pending |
| 28 | Frontend Literature | ⬜ Pending |
| 29 | Frontend Skills/Reports | ⬜ Pending |
| 30 | Integration & E2E | ⬜ Pending |
| 31 | Packaging & Deploy | ⬜ Pending |
| 32 | Evaluation | ⬜ Pending |

---

## Milestones

### Milestone 1: Foundation (Phases 1-4)

**Goal:** Working backend with database, models, API, and audit system.

**Deliverables:**
- Repository with documentation
- Backend with FastAPI
- PostgreSQL with all models
- Basic CRUD API
- Audit logging

**Verification:**
- Backend starts and connects to database
- All models created via migrations
- CRUD endpoints return correct responses

---

### Milestone 2: Academic Search (Phases 5-8)

**Goal:** Connect to scholarly sources and retrieve ranked papers.

**Deliverables:**
- Multi-provider LLM abstraction
- 8 academic source connectors
- Keyword expansion engine
- Literature retrieval and ranking

**Verification:**
- System searches OpenAlex, Semantic Scholar, Crossref, arXiv
- Papers ranked by relevance, citations, recency
- Search plans generated from ideas

---

### Milestone 3: Literature Intelligence (Phases 9-12)

**Goal:** Analyze papers, detect conflicts, generate questions.

**Deliverables:**
- Paper analysis engine (structured extraction)
- Clustering engine
- Conflict detection engine
- Research question generator

**Verification:**
- Papers analyzed with structured fields
- Papers grouped into meaningful clusters
- Conflicts detected and categorized
- Research questions generated from conflicts

---

### Milestone 4: Hypothesis and Scoring (Phases 13-16)

**Goal:** Form hypotheses, plan validation, score ideas.

**Deliverables:**
- Hypothesis generator
- Validation planner
- Idea scoring engine
- Idea ledger

**Verification:**
- Hypotheses are testable with failure conditions
- Validation plans include datasets, baselines, metrics
- Ideas scored on 12 criteria with weighted formula
- All ideas stored with version history

---

### Milestone 5: Idle Cognition (Phases 17-18)

**Goal:** Autonomous background research.

**Deliverables:**
- Skill memory system
- Idle cognition engine
- Scheduler
- 6 idle modes

**Verification:**
- System creates candidate skills
- Idle cycles start when triggered
- Each idle mode produces scored ideas
- Skills tracked by usage and performance

---

### Milestone 6: Agents and Workflows (Phases 19-20)

**Goal:** Formalized agents and durable workflows.

**Deliverables:**
- 15 specialized agents
- 6 durable workflows
- State checkpointing
- Pause/resume with approval

**Verification:**
- Each agent has defined responsibilities
- Workflows run end-to-end
- State persists across pauses
- Approval interrupts work correctly

---

### Milestone 7: Data Analysis (Phase 21)

**Goal:** Safe, reproducible data analysis.

**Deliverables:**
- Docker sandbox
- Script execution
- Artifact storage
- Result linking to hypotheses

**Verification:**
- Code executes in sandbox only
- All artifacts preserved
- Results linked to hypotheses

---

### Milestone 8: Knowledge and Reporting (Phases 22-24)

**Goal:** Persistent knowledge, reports, and safety.

**Deliverables:**
- Knowledge base and research wiki
- Report generation (Markdown, HTML, PDF)
- Approval system
- Safety enforcement

**Verification:**
- Wiki generated from structured data
- Reports produced for completed runs
- Approval queue functional
- Safety rules enforced

---

### Milestone 9: Frontend (Phases 25-29)

**Goal:** Complete web dashboard.

**Deliverables:**
- Next.js frontend with Tailwind
- Project dashboard
- Idea ledger with scores
- Paper and cluster views
- Skill browser
- Report viewer
- Approval queue

**Verification:**
- All views render correctly
- Data displays correctly
- User can navigate all sections
- Settings configurable

---

### Milestone 10: Integration and Release (Phases 30-32)

**Goal:** Full system integration and evaluation.

**Deliverables:**
- All modules connected
- End-to-end tests
- Docker deployment
- Evaluation against baselines
- Documentation complete

**Verification:**
- User-directed research works end-to-end
- Idle autonomous research works
- System proves improvement over baselines
- Installable and runnable

---

## Dependency Graph

```
Phase 1 (Repository)
  ↓
Phase 2 (Backend Foundation)
  ↓
Phase 3 (Data Model) ← Phase 4 (Research State)
  ↓
Phase 5 (LLM Providers) ← Phase 6 (Connectors)
  ↓
Phase 7 (Keyword Expansion) ← Phase 8 (Literature Retrieval)
  ↓
Phase 9 (Paper Analysis) ← Phase 10 (Clustering) ← Phase 11 (Conflicts)
  ↓
Phase 12 (Questions) ← Phase 13 (Hypotheses) ← Phase 14 (Validation)
  ↓
Phase 15 (Scoring) ← Phase 16 (Idea Ledger)
  ↓
Phase 17 (Skills) ← Phase 18 (Idle Cognition)
  ↓
Phase 19 (Agents) ← Phase 20 (Workflows)
  ↓
Phase 21 (Sandbox) ← Phase 22 (Knowledge) ← Phase 23 (Reports) ← Phase 24 (Safety)
  ↓
Phase 25-29 (Frontend)
  ↓
Phase 30 (Integration) ← Phase 31 (Deploy) ← Phase 32 (Evaluation)
```

---

## Current Status

**Current Phase:** 1 — Repository & Documentation

**Progress:** Directory structure created. Documentation files written.

**Next:** Phase 2 — Backend Foundation (Python, FastAPI, PostgreSQL, models, API)
