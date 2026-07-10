# Codebase Structure

**Analysis Date:** 2026-07-09

## Directory Layout

```
autoscience/
├── backend/                          # FastAPI Python backend
│   ├── app/
│   │   ├── api/                      # REST API routers (20 files)
│   │   │   ├── router.py            # Main API router
│   │   │   ├── projects.py          # Project CRUD
│   │   │   ├── ideas.py             # Idea management
│   │   │   ├── runs.py              # Research runs
│   │   │   ├── papers.py            # Paper management
│   │   │   ├── skills.py            # Skills + evaluation + SSE stream
│   │   │   ├── questions.py         # Research questions
│   │   │   ├── hypotheses.py        # Hypotheses + validation
│   │   │   ├── reports.py           # Reports + export
│   │   │   ├── wiki.py              # Knowledge notes + semantic search
│   │   │   ├── manuscripts.py       # Manuscripts + templates + compile
│   │   │   ├── research.py          # Research run control
│   │   │   ├── search.py            # SSE stream for workflow events
│   │   │   ├── datasets.py          # Dataset management
│   │   │   ├── approvals.py         # Approval workflow
│   │   │   ├── auth.py              # Authentication + token
│   │   │   ├── collaboration.py     # Members, comments, reviews, activity
│   │   │   ├── connectors.py        # Connector health status
│   │   │   ├── sandbox_analysis.py  # Power analysis, Plotly
│   │   │   ├── user_activity.py     # Activity tracking
│   │   │   └── organizations.py     # Organization management
│   │   ├── models/                   # SQLAlchemy models (11 files)
│   │   │   ├── base.py              # Base model (UUID, timestamps)
│   │   │   ├── project.py           # Project model
│   │   │   ├── idea.py              # Idea + IdeaVersion/IdeaScore/IdeaClassification/IdeaDecision
│   │   │   ├── paper.py             # Paper + PaperSource/Fulltext/Embedding/Analysis
│   │   │   ├── research_run.py      # ResearchRun + ResearchRunEvent/ToolCall/IdleCycle
│   │   │   ├── research_question.py # ResearchQuestion + Hypothesis + ValidationPlan
│   │   │   ├── skill.py             # Skill + SkillVersion/SkillUsage/SkillEvaluation
│   │   │   ├── report.py            # Report + KnowledgeNote/Dataset/LiteratureSearch/Analysis
│   │   │   ├── audit.py             # AuditLog + ApprovalRequest + SystemEvent
│   │   │   ├── collaboration.py     # User + ProjectMember + Comment + ReviewProposal
│   │   │   └── organization.py      # Organization model
│   │   ├── services/                 # Business logic (48 files)
│   │   │   ├── orchestrator.py      # Central research coordinator
│   │   │   ├── project_service.py
│   │   │   ├── idea_service.py
│   │   │   ├── idea_ledger_service.py
│   │   │   ├── research_run_service.py
│   │   │   ├── research_persistence_service.py
│   │   │   ├── paper_service.py
│   │   │   ├── paper_analysis_service.py
│   │   │   ├── literature_service.py
│   │   │   ├── cluster_service.py
│   │   │   ├── conflict_service.py
│   │   │   ├── question_service.py
│   │   │   ├── research_question_service.py
│   │   │   ├── hypothesis_service.py
│   │   │   ├── validation_service.py
│   │   │   ├── scoring_service.py
│   │   │   ├── safety_service.py
│   │   │   ├── skill_service.py
│   │   │   ├── skill_memory_service.py
│   │   │   ├── skill_performance_service.py
│   │   │   ├── skill_evaluation_scheduler.py
│   │   │   ├── knowledge_service.py
│   │   │   ├── report_service.py
│   │   │   ├── report_generator.py
│   │   │   ├── manuscript_service.py
│   │   │   ├── manuscript_context_service.py
│   │   │   ├── revision_workflow_service.py
│   │   │   ├── latex_compiler.py
│   │   │   ├── notebook_export_service.py
│   │   │   ├── dataset_upload_service.py
│   │   │   ├── audit_service.py
│   │   │   ├── cache_service.py
│   │   │   ├── event_stream.py      # EventBroadcaster (Redis pub/sub)
│   │   │   ├── sse_stream.py        # SSE streaming for workflow events
│   │   │   ├── auth_service.py
│   │   │   ├── oauth_service.py
│   │   │   ├── user_activity_service.py
│   │   │   ├── activity_feed_service.py
│   │   │   ├── notification_service.py
│   │   │   ├── idle_scheduler.py
│   │   │   ├── idle_cycle_service.py
│   │   │   ├── snapshot_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── wiki_embedding_service.py
│   │   │   ├── wiki_graph_service.py
│   │   │   ├── artifact_linking_service.py
│   │   │   ├── peer_review_service.py
│   │   │   └── evaluation.py
│   │   ├── engine/                  # LLM-powered engines (21 files)
│   │   │   ├── keyword_engine.py
│   │   │   ├── literature_engine.py
│   │   │   ├── paper_analysis.py
│   │   │   ├── clustering.py
│   │   │   ├── conflict_detection.py
│   │   │   ├── question_generation.py
│   │   │   ├── hypothesis_generation.py
│   │   │   ├── validation_planning.py
│   │   │   ├── scoring.py
│   │   │   ├── deduplication.py
│   │   │   ├── idle_cognition.py
│   │   │   ├── manuscript_engine.py
│   │   │   ├── claims_pipeline.py
│   │   │   ├── effect_size_extraction.py
│   │   │   ├── sandbox_generator.py
│   │   │   ├── power_analysis.py
│   │   │   ├── domain_packs.py
│   │   │   ├── journal_templates.py
│   │   │   └── latex_numbering.py
│   │   ├── agents/                  # Agent configurations
│   │   │   └── base.py             # Base agent class + all persona configs
│   │   ├── llm/                     # LLM provider integrations
│   │   │   ├── base.py             # Base LLM provider interface
│   │   │   ├── router.py           # LLM request router with failover
│   │   │   ├── openai_provider.py
│   │   │   ├── anthropic_provider.py
│   │   │   ├── openrouter_provider.py
│   │   │   ├── local_provider.py
│   │   │   ├── llamacpp_provider.py
│   │   │   └── prompts/            # Prompt templates
│   │   ├── connectors/              # Academic source connectors (16 files)
│   │   │   ├── base.py             # AcademicConnector interface
│   │   │   ├── manager.py          # ConnectorManager with parallel search
│   │   │   ├── arxiv.py
│   │   │   ├── semantic_scholar.py
│   │   │   ├── openalex.py
│   │   │   ├── crossref.py
│   │   │   ├── pubmed.py
│   │   │   ├── doaj.py
│   │   │   ├── core.py
│   │   │   ├── unpaywall.py
│   │   │   ├── searxng.py
│   │   │   ├── firecrawl.py
│   │   │   ├── dataset_connectors.py
│   │   │   └── serialization.py
│   │   ├── workflows/               # Workflow orchestration
│   │   │   ├── research_workflow.py # 17-step research workflow
│   │   │   └── safety_gates.py     # Approval checkpoints
│   │   ├── sandbox/                 # Code execution sandbox
│   │   │   ├── __init__.py
│   │   │   └── executor.py         # Docker-based script execution
│   │   ├── schemas/                 # Pydantic validation schemas (15 files)
│   │   │   ├── base.py, project.py, idea.py, paper.py, skill.py
│   │   │   ├── research_run.py, research_state.py, research_question.py
│   │   │   ├── report.py, manuscript.py, audit.py, dataset.py
│   │   │   ├── collaboration.py, validation.py, organization.py
│   │   ├── middleware/              # FastAPI middleware
│   │   ├── app/config.py           # Pydantic settings
│   │   ├── app/database.py         # DB session management
│   │   └── app/dependencies.py     # FastAPI dependency injection
│   ├── alembic/                    # DB migrations
│   │   └── versions/
│   ├── tests/                      # Python tests
│   │   ├── conftest.py
│   │   ├── test_api/
│   │   ├── test_services/
│   │   ├── test_engine/
│   │   ├── test_engines/
│   │   ├── test_models/
│   │   ├── test_connectors/
│   │   ├── test_agents/
│   │   ├── test_llm/
│   │   ├── test_migrations/
│   │   ├── test_integration/
│   │   └── test_workflows/
│   ├── scripts/                    # Utility scripts
│   ├── Dockerfile, Dockerfile.dev
│   └── pyproject.toml
├── frontend/                       # Next.js React frontend
│   ├── src/
│   │   ├── app/                    # App Router pages
│   │   │   ├── page.tsx           # Homepage
│   │   │   ├── layout.tsx         # Root layout
│   │   │   ├── providers.tsx      # Context providers
│   │   │   ├── globals.css        # Global styles + theme vars
│   │   │   └── projects/
│   │   │       ├── page.tsx       # Project list
│   │   │       └── [id]/
│   │   │           ├── page.tsx   # Project dashboard
│   │   │           ├── pipeline/  # Research pipeline view
│   │   │           ├── ideas/     # Idea ledger
│   │   │           ├── papers/    # Paper views
│   │   │           ├── clusters/  # Cluster visualization
│   │   │           ├── questions/ # Question navigator
│   │   │           ├── hypotheses/ # Hypothesis workshop
│   │   │           ├── reports/   # Research reports
│   │   │           ├── wiki/      # Knowledge wiki
│   │   │           ├── skills/    # Skills + eval settings + history
│   │   │           ├── manuscripts/ # Article studio
│   │   │           ├── datasets/  # Dataset browser
│   │   │           ├── approval/  # Approval requests
│   │   │           ├── settings/  # Project settings
│   │   │           ├── runs/      # Research runs
│   │   │           ├── studio/[runId]/ # Run studio
│   │   │           ├── health/    # Cognitive health dashboard
│   │   │           ├── team/      # Team management
│   │   │           └── article-studio/ # Article writing
│   │   ├── components/
│   │   │   ├── layout/            # Layout components
│   │   │   │   ├── Layout.tsx, Header.tsx, Sidebar.tsx
│   │   │   │   ├── MobileTopBar.tsx, ArtifactPanel.tsx
│   │   │   │   ├── NotificationBell.tsx, ShortcutOverlay.tsx
│   │   │   ├── ui/                # Reusable UI (43 components)
│   │   │   │   ├── Button.tsx, Card.tsx, Input.tsx, Modal.tsx
│   │   │   │   ├── Table.tsx, Tabs.tsx, Badge.tsx, Skeleton.tsx
│   │   │   │   ├── toast.tsx, EmptyState.tsx, LoadState.tsx
│   │   │   │   ├── CognitiveEntropy.tsx, FocusMetric.tsx
│   │   │   │   ├── ConflictHeatmap.tsx, ConflictDensity.tsx
│   │   │   │   ├── NoveltyDistribution.tsx, IdeaTimeline.tsx
│   │   │   │   ├── SkillRate.tsx, SkillPerformancePanel.tsx
│   │   │   │   ├── SkillPerformanceChart.tsx
│   │   │   │   ├── SkillEvalSettings.tsx, SkillEvalHistory.tsx
│   │   │   │   ├── DecisionGate.tsx, DiscoveryWizard.tsx
│   │   │   │   ├── ManuscriptEditor.tsx, ManuscriptPreview.tsx
│   │   │   │   ├── DatasetBrowser.tsx, ValidationPlanEditor.tsx
│   │   │   │   ├── SandboxEditor.tsx, ResultsViewer.tsx
│   │   │   │   ├── ArtifactGallery.tsx, KnowledgeCard.tsx
│   │   │   │   ├── KnowledgeGraph.tsx, SemanticMap.tsx
│   │   │   │   ├── CitationGraph.tsx, PaperComparison.tsx
│   │   │   │   ├── ThinkingTree.tsx, ProjectCreationWizard.tsx
│   │   │   │   ├── GenerateManuscriptButton.tsx, LaTeXPrism.tsx
│   │   │   │   ├── StatCard.tsx, CommandPalette.tsx
│   │   │   │   └── search-bar.tsx
│   │   ├── hooks/                 # React hooks (4 files)
│   │   │   ├── useAsyncData.ts
│   │   │   ├── use-keyboard-shortcuts.ts
│   │   │   ├── use-activity-heartbeat.ts
│   │   │   └── use-skill-eval-stream.ts
│   │   └── lib/                   # Utilities
│   │       ├── api.ts             # Full API client
│   │       ├── types.ts           # All TypeScript interfaces
│   │       ├── utils.ts
│   │       └── settingsVault.ts   # Encrypted API key vault
│   ├── e2e/
│   │   └── smoke.spec.ts          # Playwright smoke test
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── vitest.config.ts
│   ├── playwright.config.ts
│   └── package.json
├── docker/
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   └── Dockerfile.sandbox
├── knowledge/                     # Documentation/notes
├── .github/workflows/
│   └── ci.yml                     # GitHub Actions CI
├── .planning/                     # Planning docs (12 files)
│   ├── codebase/                  # Codebase reference docs
│   ├── REQUIREMENTS.md
│   ├── ROADMAP.md, ROADMAP_V2.1.md
│   ├── PROJECT.md
│   └── IMPLEMENTATION_SUMMARY.md
└── external/                      # External reference projects
    ├── fireplexity/
    ├── firesearch/
    └── open-researcher/
```

## Where to Add New Code

**New Feature:**
- Backend: API router in `api/`, service in `services/`, model in `models/`, schema in `schemas/`
- Frontend: Page under `app/projects/[id]/<feature>/page.tsx`, component in `components/ui/`

**New Component:**
- React: `components/ui/<ComponentName>.tsx` + export from `components/ui/index.ts`
- Python service: `services/<service_name>.py`
- DB model: `models/<model_name>.py` + register in `models/__init__.py`

**New API Endpoint:**
- Add method to existing router in `api/` or create new router file + register in `api/router.py`
- Add frontend method in `lib/api.ts` + type in `lib/types.ts`

*Structure analysis: 2026-07-09*
