# Requirements: Deep Academic Research, Experiment, and Article Studio

## Executive Summary

Transform Autoscience into a complete scientific cognition studio with three integrated modes:
1. **Research Mode** - Deep literature investigation and gap analysis
2. **Experiment Mode** - Data analysis, validation, and empirical testing
3. **Article Mode** - Scientific manuscript composition and publication preparation

---

## 1. Research Mode Requirements

### 1.1 Multi-Source Literature Search (COMPLETE)
- [x] arXiv connector (full implementation)
- [x] Semantic Scholar connector (full implementation)
- [x] OpenAlex connector (full implementation)
- [x] PubMed connector (full implementation, XML parsing)
- [x] Crossref connector (full implementation, works/references/citations)
- [x] DOAJ connector (full implementation, open access journals)
- [x] CORE connector (full implementation with API key)
- [x] Unpaywall connector (DOI lookup, OA status)
- [x] SearXNG federated search (optional)
- [x] Firecrawl web scraping (optional)
- [x] Caching support (Redis via CacheService)
- [x] ConnectorManager with parallel search, dedup, and health checks

### 1.2 Paper Analysis Engine (COMPLETE)
- [x] Abstract analysis pipeline
- [x] Fulltext extraction (when available)
- [x] Structured extraction (problem, method, findings, limitations)
- [x] Claim extraction with evidence linking
- [x] Method comparison engine
- [x] Future work extraction
- [x] Assumption detection

### 1.3 Conflict Detection (COMPLETE)
- [x] Finding conflicts
- [x] Method conflicts
- [x] Dataset conflicts
- [x] Assumption conflicts
- [x] Scope conflicts
- [x] Recency conflicts
- [x] Theory-practice conflicts

### 1.4 Research Question Generator (COMPLETE)
- [x] Gap-to-question transformation
- [x] Adjacent-field collisions
- [x] Dataset discovery triggers
- [x] Cross-domain question generation

---

## 2. Experiment Mode Requirements

### 2.1 Dataset Discovery and Management (COMPLETE)
- [x] Dataset search across repositories (HuggingFace, Zenodo, Kaggle)
- [x] Dataset metadata extraction
- [x] Dataset preview generation (head, schema)
- [x] Dataset upload with validation (CSV/JSON, BOM handling, schema inference)
- [x] Dataset provenance tracking (original filename, uploader metadata)
- [x] CSV/JSON/JSONL file upload with format validation
- [x] Dataset export (JSON, CSV)
- [x] External dataset fetch from HuggingFace/Zenodo

### 2.2 Validation Experiment Designer (COMPLETE)
- [x] Validation plan generation (from hypotheses)
- [x] Baseline identification
- [x] Cost estimation
- [x] Difficulty assessment
- [x] Statistical power analysis (API endpoint)
- [x] Simulation design
- [x] Metrics and statistical tests specification

### 2.3 Data Analysis Sandbox (COMPLETE)
- [x] Docker sandbox infrastructure
- [x] Python script generation from validation plans
- [x] Safe execution with resource limits
- [x] Artifact capture (figures, tables)
- [x] Statistical test library (t-tests, ANOVA, effect sizes)
- [x] Plotly visualization sandbox (API endpoint)
- [x] Jupyter notebook export from sandbox
- [x] Reproducibility guarantees (captured scripts, results, artifacts)

### 2.4 Results Synthesis (COMPLETE)
- [x] Experimental results extraction (regex + LLM two-stage)
- [x] Hypothesis validation/refutation
- [x] Effect size calculation (Cohen's d, η², R², r, etc.)
- [x] Statistical significance reporting
- [x] Results-to-claims pipeline (structured claims extraction)
- [x] Cross-mode artifact linking (experiment → manuscript)

---

## 3. Article Mode Requirements

### 3.1 Manuscript Generator (COMPLETE)
- [x] IMRaD structure (Introduction, Methods, Results, Discussion)
- [x] Title generation
- [x] Abstract composition
- [x] Introduction drafting (context, gap, contribution)
- [x] Methods section (from validation plans)
- [x] Results section (from experimental data, effect sizes, claims)
- [x] Discussion section (interpretation, limitations, future work)
- [x] References management
- [x] Cross-mode artifact linking (experiment artifacts → manuscript sections)
- [x] Structured claims and effect sizes injection

### 3.2 Citation System (COMPLETE)
- [x] BibTeX export
- [x] Bibliography generation
- [x] Citation DOI resolution
- [x] Reference formatting (APA, MLA, Chicago, IEEE)
- [x] Citation key generation

### 3.3 LaTeX Integration (COMPLETE)
- [x] LaTeX template system (IEEE, Nature, ACL templates)
- [x] Equation rendering (inline $$ and display math)
- [x] Figure placeholder management (auto-numbering)
- [x] Table auto-numbering
- [ ] Overleaf sync (optional — not implemented)
- [x] PDF export (via pdflatex when available)

### 3.4 Multi-Format Export (COMPLETE)
- [x] LaTeX export (main.tex + references.bib)
- [x] Markdown export (with LaTeX→MD conversion)
- [x] HTML export with styling (Georgia/serif layout)
- [x] PDF export (via pdflatex)
- [x] DOCX export (via pandoc when available)
- [x] ZIP bundle (LaTeX + BibTeX)

---

## 4. Core Infrastructure Requirements

### 4.1 Cognitive Health Dashboard (COMPLETE)
- [x] Cognitive entropy visualization (animated bar with mode badges)
- [x] Focus metric (depth vs breadth with gauge display)
- [x] Idea evolution timeline (IdeaTimeline component)
- [x] Skill utilization rate (SkillRate component with usage stats)
- [x] Conflict density indicator (by-type breakdown, severity)
- [x] Novelty score distribution (NoveltyDistribution component)
- [x] Conflict heatmap (grid with type×cluster, filtering, tooltips)
- [x] Refresh/real-time update capability

### 4.2 Real-time Observability (COMPLETE)
- [x] Server-Sent Events (SSE) for workflow updates
- [x] Event stream with pub/sub (Redis-backed)
- [x] Thinking tree visualization (real-time reasoning display)
- [x] Agent handoff/phase change notifications
- [x] Live paper count updates via SSE events
- [x] Activity feed (project-level event log)
- [x] Skill evaluation event broadcasting via SSE (Redis pub/sub channel)
- [x] SSE endpoint for system evaluation events (`/skills/performance/eval-stream`)
- [x] Frontend hook for real-time evaluation toasts (`useSkillEvalStream`)

### 4.3 Approval Safety System (COMPLETE)
- [x] Approval request model (action_type, payload, status)
- [x] DecisionGate component (pending/approved/rejected states)
- [x] Spend threshold enforcement ($1.00+ triggers approval gate)
- [x] External publish approval workflow
- [x] Major pivot approval
- [x] Approval history tracking (archived decisions view)
- [x] Budget tracking (per-run and daily limits)
- [x] Safety policy (always_allowed / approval_required / never_allowed)
- [x] Step-level gating in research workflow (safety_gates.py)
- [x] Auto-resume workflow after approval

### 4.4 Skill Memory System (COMPLETE)
- [x] Skill schemas (Skill, SkillVersion, SkillUsage, SkillEvaluation)
- [x] Skill creation (candidate → tested → active lifecycle)
- [x] Skill retrieval by context (keyword-based relevance scoring)
- [x] Skill search (by name, purpose, type, status, min usage)
- [x] Skill performance tracking (times_used, successful_uses, avg_score_improvement)
- [x] Skill versioning system (incremented on procedure changes)
- [x] Skill deprecation workflow (deprecated → retired lifecycle)
- [x] Skill evaluation (system-rated with feedback)
- [x] Auto-promotion (candidate → tested after 3 successful uses)
- [x] Skill statistics (by_status, by_type, avg_usage, avg_success_rate)
- [x] Scheduled skill evaluation (asyncio background loop)
- [x] Runtime scheduler configuration API (enable/disable, interval, dry run)
- [x] Scheduler settings UI (master toggle, interval selector 1h–72h, dry run mode)
- [x] Manual evaluation trigger with SSE broadcast (Run Now button)
- [x] Evaluation notification history panel (audit-log-backed event list)

---

## 5. Frontend Requirements

### 5.1 Studio Layout (COMPLETE)
- [x] Amber/Sage design system
- [x] Glass morphism surfaces
- [x] Responsive layout (mobile sidebar drawer + top bar)
- [x] Dark/light mode toggle (next-themes + ThemeToggle)
- [x] Keyboard navigation (shortcuts with overlay)
- [x] Command palette (Cmd+K with project page navigation)

### 5.2 Research Studio (COMPLETE)
- [x] Project dashboard (stats, quick actions, navigation)
- [x] Idea ledger (list, score, classify, filter)
- [x] Paper views (list, detail, comparison, citation graph)
- [x] Cluster visualization (thematic grouping, labels)
- [x] Conflict heatmap (grid with severity colors, filtering, tooltips)
- [x] Question navigator (list with rank, status, rejection reasons)
- [x] Hypothesis workshop (detailed view, validation plans, falsification)

### 5.3 Experiment Studio (COMPLETE)
- [x] Dataset browser (search, metadata, preview, add to project)
- [x] Validation plan editor (metrics, baselines, datasets, design)
- [x] Sandbox code editor (via Plotly sandbox + power analysis UIs)
- [x] Results viewer (experiment telemetry, stdout/stderr, artifacts)
- [x] Artifact gallery (experiment outputs visualization)

### 5.4 Article Studio (COMPLETE)
- [x] Manuscript editor (LaTeX with syntax highlighting)
- [x] Citation manager (BibTeX generation)
- [x] LaTeX preview (tab-based: LaTeX, Preview, References)
- [x] Export controls (LaTeX, PDF, DOCX, MD, HTML, ZIP)
- [x] Journal template application (IEEE, Nature, ACL)
- [ ] Collaboration mode (real-time editing — not implemented)

---

## 6. Integration Requirements

### 6.1 Seamless Workflow (IMPLEMENTED)
- [x] Research → Experiment handoff (ideas → hypotheses → validation plans)
- [x] Experiment → Article handoff (validation results → manuscript sections)
- [x] Article → Research (revision cycle via revision workflow service)
- [x] Cross-mode artifact linking (experiment figures/tables → manuscript)
- [x] Revision workflow (spawn revision run from manuscript → generate revised manuscript)

### 6.2 Export Integration (COMPLETE)
- [x] Report generation from any mode (research reports, manuscripts)
- [x] Knowledge base update from all modes (wiki notes for papers, clusters, conflicts)
- [x] Skill extraction from successful patterns (auto-promotion, evaluation)
- [x] Manuscript compilation → PDF via server-side pdflatex

---

## Remaining Items

| Item | Impact | Notes |
|------|--------|-------|
| Overleaf sync | Low | Would require OAuth + API integration with Overleaf |
| Collaboration mode (real-time editing) | Medium | Would require operational transform or CRDT |
| JSON raw data export | Low | Trivial addition to existing export endpoints |

---

## Priority Matrix

| Priority | Feature | Impact | Effort |
|----------|---------|--------|--------|
| P0 | Complete paper analysis extraction | High | Medium |
| P0 | Citation system (BibTeX, bibliography) | High | Medium |
| P0 | Dataset discovery connectors | High | Large |
| P0 | Manuscript generator (IMRaD) | High | Large |
| P0 | Approval safety gates & spend enforcement | High | Medium |
| P0 | Skill memory & evaluation system | High | Large |
| P1 | Real-time SSE updates | Medium | Medium |
| P1 | Validation experiment sandbox | High | Large |
| P1 | LaTeX integration | Medium | Medium |
| P1 | Cross-mode artifact linking | Medium | Medium |
| P2 | Overleaf sync | Low | Medium |
| P2 | Collaboration mode | Medium | Large |

---
*Requirements analysis: 2026-07-09 (updated to reflect actual codebase state)*
