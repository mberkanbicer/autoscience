---
name: Autoscience Studio
version: 2.6.0
soul: "Deep Academic Research, Experiment, and Article Studio — A complete cognitive laboratory for researchers and scientists"
status: stable
created: 2026-06-05
updated: 2026-07-09

## Vision

Transform Autoscience into a **comprehensive Deep Academic Research, Experiment, and Article Studio** that provides everything a researcher and scientist needs:

1. **Deep Literature Research** — Multi-source academic search, paper analysis, conflict detection, question generation, hypothesis formation
2. **Experimental Design** — Dataset discovery, validation planning, statistical analysis, sandboxed code execution
3. **Article Writing** — Scientific manuscript generation (IMRaD), LaTeX integration, citation management, multi-format export
4. **Research Management** — Idea ledger, cognitive health dashboard, skill memory, approval workflows, knowledge base

## Core Capabilities

| Capability | Status | Notes |
|------------|--------|-------|
| Multi-source Literature Search | Complete | 8 connectors: arXiv, Semantic Scholar, OpenAlex, PubMed, Crossref, DOAJ, CORE, Unpaywall + SearXNG/Firecrawl optional |
| Paper Analysis & Extraction | Complete | Claims, methods, limitations, assumptions, future work |
| Conflict Detection | Complete | 8 types across papers with heatmap visualization |
| Question Generation | Complete | From conflicts, gaps, adjacent-field collisions |
| Hypothesis Formation | Complete | With falsification criteria, validation planning, power analysis |
| Dataset Discovery & Management | Complete | HuggingFace, Zenodo, Kaggle + upload with validation, preview, export |
| Validation Experiments | Complete | Docker sandbox, Python script gen, Plotly, Jupyter export, artifact capture |
| Manuscript Generation | Complete | IMRaD structure + CitationManager + revision workflow |
| Citation Management | Complete | BibTeX, DOI resolution, APA/MLA/Chicago/IEEE formatting |
| Skill Memory & Evaluation | Complete | Full lifecycle (candidate→tested→active→deprecated→retired), background scheduler, runtime config, settings UI |
| Cognitive Health Dashboard | Complete | Entropy, focus, timeline, skill rate, novelty, conflict heatmap |
| Real-time Observability | Complete | SSE with Redis pub/sub, thinking tree, activity feed, skill eval event broadcast |
| Knowledge Wiki | Complete | Text + semantic embedding search, cross-run knowledge graph |
| Approval Safety System | Complete | Spend thresholds, DecisionGate, budget tracking, auto-resume |
| Collaboration | Complete | Multi-user projects, RBAC (viewer/editor/admin), review workflows, OAuth (Google/GitHub) |
| Publication Pipeline | Complete | Journal templates (IEEE/Nature/ACL), multi-format export (LaTeX/PDF/DOCX/MD/HTML/ZIP), PDF compile |

## Architecture

- **Frontend**: Next.js 14 + React + TypeScript + Tailwind CSS + lucide-react + recharts
- **Backend**: FastAPI + Python 3.11 + SQLAlchemy (async) + PostgreSQL + Redis
- **LLM Providers**: OpenAI, Anthropic, OpenRouter, Local (Ollama), Llama.cpp (pluggable router with failover)
- **Academic Sources**: arXiv, Semantic Scholar, OpenAlex, PubMed, Crossref, DOAJ, CORE, Unpaywall (8 connectors) + SearXNG/Firecrawl (optional)
- **Dataset Sources**: HuggingFace, Zenodo, Kaggle
- **Sandbox**: Docker-based isolated code execution with resource limits
- **Auth**: JWT Bearer tokens + OAuth (Google, GitHub) + header-based local fallback
- **CI/CD**: GitHub Actions, Docker Compose
- **Testing**: pytest (backend), vitest (frontend unit), Playwright (E2E)

## Milestone Progress

| Milestone | Focus | Status |
|-----------|-------|--------|
| v2.0 | Research Studio Foundation | COMPLETE |
| v2.1 | Production Hardening | COMPLETE |
| v2.2 | Collaboration & OAuth | COMPLETE |
| v2.3 | Publication Pipeline | COMPLETE |
| v2.4 | Domain Specialization | COMPLETE |
| v2.5 | Polish & Hardening | COMPLETE |
| v2.6 | Skill Evaluation & Scheduler Control | COMPLETE |

## Remaining Backlog

| Item | Impact | Effort |
|------|--------|--------|
| Overleaf sync | Low | Medium |
| Collaboration mode (real-time editing) | Medium | Large |
| JSON raw data export | Low | Trivial |

---

*Project charter: 2026-07-09 (v2.6.0)*
