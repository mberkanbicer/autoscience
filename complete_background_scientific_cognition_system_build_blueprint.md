# Complete Build Blueprint: Background Scientific Cognition System

## Document Purpose

This document defines a complete, production-oriented build plan for the project.

The goal is not to create a small prototype or minimum viable product. The goal is to build a complete, fully functional research system that behaves like a persistent researcher’s brain: it monitors scientific literature, generates ideas during idle periods, detects conflicts, forms hypotheses, analyzes evidence and data, scores ideas, rejects weak directions, and learns reusable research skills from every cycle.

The system will be called here: **Background Scientific Cognition System**.

Alternative names:

- Autonomous Scientific Research Brain
- Self-Learning Research Agent
- Researcher Brain OS
- Continuous Research Intelligence System
- Autonomous Literature-Grounded Hypothesis Engine

---

## 1. Core Product Vision

The system should function as a digital research mind.

It should not merely answer prompts. It should maintain a continuing research life.

It should:

1. Receive user ideas and research them.
2. Detect how flexible the user is about the idea.
3. Follow strict prompts narrowly when the user is specific.
4. Adapt and improve ideas when the user allows flexibility.
5. Start autonomous idle research when the project is active but no user task is running.
6. Monitor recent scientific literature.
7. Find high-impact papers, recent frontier papers, review papers, and contradictory papers.
8. Cluster papers into themes.
9. Detect scientific tensions, conflicts, assumptions, and gaps.
10. Generate research questions from those tensions.
11. Convert questions into testable hypotheses.
12. Design validation plans.
13. Analyze datasets or run simulations when appropriate.
14. Score ideas.
15. Classify ideas as high-value, promising, incremental, weak, or reject.
16. Store every idea, including rejected ones, with reasons.
17. Create reusable skills from successful and failed research cycles.
18. Use those skills in future research.
19. Keep a full audit trail of what it tried, why, what happened, and what decision it made.
20. Remain bounded by safety, cost, access, and permission rules.

---

## 2. System Identity

The system is not simply an autonomous agent.

It is a long-running scientific cognition platform with memory, curiosity, literature awareness, skepticism, hypothesis formation, validation planning, data analysis, idea judgment, skill learning, idle-time research, reproducibility, and auditability.

The system’s central loop is:

```text
Observe → Assimilate → Cluster → Detect Tension → Ask Questions → Form Hypotheses → Validate → Judge → Remember → Learn → Repeat
```

---

## 3. Reference Projects and How They Inform This Build

This project should be built as an original system, but it should borrow proven patterns from existing repositories.

### 3.1 Primary Conceptual Reference: ScienceClaw

ScienceClaw is useful as a conceptual reference because it focuses on a self-evolving AI research colleague, persistent research memory, skill evolution, scientific workflows, and citation discipline.

Borrow:

- Research-specific skill memory
- Persistent scientific context
- Citation-grounded behavior
- Domain adaptation
- Anti-hallucination rules
- Long-duration research protocols

Do not blindly copy the whole architecture. Our system is more specifically centered on idea lifecycle management, idle background cognition, conflict-derived research questions, and explicit idea rejection/valuation.

### 3.2 Primary Engineering Reference: DeerFlow

DeerFlow is useful as an engineering reference for long-horizon agent orchestration.

Borrow:

- Subagent orchestration
- Sandbox execution
- Memory handling
- Skill usage
- Tool gateway
- Long-running task architecture

### 3.3 Research Lifecycle References: freephdlabor, Agent Laboratory, AI-Scientist

Borrow:

- Literature review workflow
- Hypothesis generation
- Experiment planning
- Report and paper generation
- Review and proofreading agents
- Scientific task decomposition

Modify:

- Make the system more memory-driven.
- Make idea scoring and rejection central.
- Avoid making “paper generation” the first goal.

### 3.4 Skill Learning Reference: SkillX

SkillX is relevant for the skill system.

Borrow the three-level hierarchy:

```text
Planning skills: high-level research strategies.
Functional skills: reusable multi-step routines.
Atomic skills: small tool-use or execution patterns.
```

Apply this to scientific research.

### 3.5 Idle Ideation Reference: Open Collider

Open Collider is relevant for non-obvious idea generation.

Borrow:

- Cross-domain collision logic
- Structured creativity
- Mechanism transfer from distant domains

Use it as one of several idea-generation modes, not as the whole system.

### 3.6 Knowledge Base Reference: WeKnora

WeKnora is relevant as a knowledge-base and RAG platform.

Borrow:

- Research wiki
- Document understanding
- Semantic retrieval
- Knowledge graph
- Self-maintaining knowledge base

### 3.7 Research State Reference: PhysicsIntern

PhysicsIntern is relevant because it uses structured research state.

Borrow:

- Explicit state object
- Snapshotting
- Self-review
- Critic/reviewer roles
- Reproducibility mindset

---

## 4. Final System Architecture

The complete system should have the following major components:

1. User Interface
2. Project Manager
3. Research Orchestrator
4. Autonomy and Flexibility Engine
5. Idle Cognition Engine
6. Literature Intelligence Engine
7. Paper Ingestion and Parsing Engine
8. Paper Clustering Engine
9. Conflict and Gap Detection Engine
10. Research Question Generator
11. Hypothesis Generator
12. Validation Planner
13. Data Analysis Sandbox
14. Idea Scoring Engine
15. Idea Ledger
16. Skill Memory
17. Knowledge Base / Research Wiki
18. Multi-Agent Runtime
19. Tool Gateway
20. Permissions and Safety Layer
21. Logging and Audit System
22. Reporting and Export System
23. Evaluation and Benchmarking System
24. Deployment and Operations Layer

---

## 5. Recommended Technology Stack

### 5.1 Backend

Recommended stack:

- Python
- FastAPI
- PostgreSQL
- pgvector or Qdrant
- Redis
- Celery, RQ, Dramatiq, or APScheduler
- Docker
- Playwright for controlled browser automation
- Pydantic for schema validation
- SQLAlchemy or SQLModel for database access

Reasoning:

Python is well-suited for AI, academic APIs, data analysis, scientific computing, and agent workflows.

PostgreSQL provides reliable structured storage.

pgvector or Qdrant supports semantic retrieval over papers, notes, ideas, and skills.

Redis and a task queue support long-running research jobs.

Docker is needed for safe execution of code and data analysis.

### 5.2 Agent Orchestration

Recommended:

- LangGraph for durable, stateful, resumable workflows
- OpenAI Agents SDK for agent definitions, tools, handoffs, guardrails, and tracing
- Optional: use DeerFlow as engineering reference or partial substrate if compatible

Recommended approach:

Use LangGraph-style state graphs for core research workflows, because the project needs long-running state, interrupts, resumption, and human-in-the-loop approval.

Use an agent SDK-style layer for specialized agents and tool calls.

### 5.3 Academic Data Sources

Initial sources:

- OpenAlex
- Semantic Scholar
- Crossref
- arXiv
- PubMed / Europe PMC for biomedical areas
- DOAJ
- CORE
- Unpaywall

Later sources:

- IEEE Xplore API, if access is available
- Elsevier ScienceDirect API, if access is available
- Wiley API or allowed access routes
- Taylor & Francis API or allowed access routes
- Journal RSS feeds and TOCs
- Institutional library integrations
- Zotero integration

Avoid:

- Scraping Google Scholar directly
- Scraping paywalled publisher content without permission
- Bypassing access restrictions

### 5.4 Frontend

Recommended:

- Next.js or React
- Tailwind CSS
- Charting library
- Markdown preview
- Paper table UI
- Research timeline UI
- Skill browser
- Idea ledger dashboard
- Project settings panel

### 5.5 Data Analysis

Recommended:

- Python sandbox
- Pandas
- NumPy
- SciPy
- scikit-learn
- matplotlib
- statsmodels
- Jupyter-compatible notebooks
- Docker isolation
- Reproducible script storage

---

## 6. Core Data Model

The system should be database-first, not chat-history-first.

Recommended tables:

```text
users
projects
project_settings
research_runs
research_run_events
ideas
idea_versions
idea_scores
idea_classifications
idea_decisions
idle_cycles
literature_searches
search_queries
papers
paper_sources
paper_fulltexts
paper_embeddings
paper_analyses
paper_clusters
cluster_conflicts
research_questions
hypotheses
validation_plans
datasets
analysis_runs
analysis_artifacts
skills
skill_versions
skill_usage
skill_evaluations
research_reports
knowledge_notes
audit_logs
tool_calls
approval_requests
system_events
```

---

## 7. Key Object Schemas

### 7.1 Project Schema

```json
{
  "project_id": "proj_001",
  "name": "Autonomous Scientific Research Brain",
  "domain": "AI research automation",
  "subject_scope": [
    "autonomous research agents",
    "scientific discovery automation",
    "literature-based discovery",
    "hypothesis generation"
  ],
  "out_of_scope": [
    "unrelated consumer apps",
    "military applications",
    "private medical diagnosis"
  ],
  "default_flexibility": 0.6,
  "idle_research_enabled": true,
  "idle_trigger_minutes": 120,
  "max_idle_cycles_per_day": 3,
  "max_sources_per_cycle": 50,
  "approval_required_for_external_actions": true
}
```

### 7.2 Idea Schema

```json
{
  "idea_id": "idea_001",
  "project_id": "proj_001",
  "origin": "user_prompt | idle_generated | literature_gap | skill_generated | revived_rejected_idea",
  "initial_text": "An agent that researches during idle time.",
  "current_text": "A background scientific cognition system that detects conflicts in literature and generates hypotheses.",
  "flexibility": 0.75,
  "status": "active | archived | rejected | promoted | under_validation",
  "classification": "high_value | promising | incremental | weak | reject",
  "overall_score": 7.6,
  "reason": "The idea combines idle research, conflict detection, hypothesis generation, and skill memory in a differentiated way."
}
```

### 7.3 Research Run Schema

```json
{
  "run_id": "run_001",
  "project_id": "proj_001",
  "idea_id": "idea_001",
  "run_type": "user_directed | flexible_user | idle_autonomous | validation | skill_refinement",
  "state": "created | running | paused | waiting_for_approval | completed | failed | cancelled",
  "started_at": "timestamp",
  "completed_at": "timestamp",
  "budget": {
    "max_minutes": 60,
    "max_sources": 50,
    "max_cost_usd": 5
  }
}
```

### 7.4 Skill Schema

```json
{
  "skill_id": "skill_001",
  "name": "Citation-Conflict Research Question Generator",
  "skill_type": "planning | functional | atomic | domain | evaluation | reporting | data_analysis",
  "purpose": "Generate research questions by finding contradictions among influential and recent papers.",
  "trigger_conditions": [
    "idle research cycle",
    "user asks for new research questions",
    "field has enough recent literature"
  ],
  "inputs": [
    "subject",
    "paper set",
    "clusters",
    "conflicts"
  ],
  "procedure": [
    "Retrieve high-impact papers from the past 5 years.",
    "Retrieve frontier papers from the past 12 months.",
    "Cluster papers into themes.",
    "Extract conflicting findings.",
    "Generate research questions from conflicts.",
    "Score questions and convert top candidates into hypotheses."
  ],
  "outputs": [
    "paper table",
    "cluster map",
    "conflict list",
    "research questions",
    "hypotheses",
    "idea scores"
  ],
  "status": "candidate | active | deprecated | retired",
  "version": "1.0",
  "performance": {
    "times_used": 0,
    "successful_uses": 0,
    "average_score_improvement": null
  }
}
```

---

## 8. Agent Roles

The complete system should use specialized agents.

### 8.1 Orchestrator Agent

Controls the run.

Responsibilities:

- Select workflow
- Track state
- Assign tasks to subagents
- Enforce budgets
- Pause when approval is required
- Resume workflows
- Ensure logging

### 8.2 User Intent Agent

Interprets user prompts.

Responsibilities:

- Extract topic
- Determine strictness
- Estimate flexibility
- Identify constraints
- Identify expected output
- Detect if the prompt belongs to an existing project

### 8.3 Idle Cognition Agent

Runs during idle periods.

Responsibilities:

- Select idle mode
- Generate candidate ideas
- Monitor literature
- Revisit old ideas
- Trigger research runs
- Avoid repetition

### 8.4 Literature Agent

Searches scholarly sources.

Responsibilities:

- Generate search queries
- Query academic APIs
- Normalize metadata
- Retrieve abstracts and full text when allowed
- Rank papers

### 8.5 Paper Analyst Agent

Reads papers and extracts structured claims.

Responsibilities:

- Extract findings
- Extract methods
- Extract datasets
- Extract metrics
- Extract limitations
- Extract future work
- Relate paper to current idea

### 8.6 Cluster Agent

Groups papers.

Responsibilities:

- Create thematic clusters
- Detect methodological clusters
- Detect dataset clusters
- Detect claim clusters
- Identify representative papers

### 8.7 Conflict Agent

Finds tensions.

Responsibilities:

- Detect conflicting findings
- Detect assumption conflicts
- Detect method conflicts
- Detect metric conflicts
- Detect dataset conflicts
- Detect theory-practice gaps

### 8.8 Research Question Agent

Creates questions from conflicts.

Responsibilities:

- Generate research questions
- Remove duplicates
- Rank questions
- Link questions to evidence

### 8.9 Hypothesis Agent

Turns questions into testable hypotheses.

Responsibilities:

- Define hypothesis
- Define variables
- Define expected effect
- Define assumptions
- Define failure conditions

### 8.10 Validation Planner Agent

Designs tests.

Responsibilities:

- Find datasets
- Recommend baselines
- Recommend metrics
- Propose experiments
- Propose simulations
- Define success and failure criteria

### 8.11 Data Analyst Agent

Runs safe analysis.

Responsibilities:

- Prepare datasets
- Run scripts
- Analyze results
- Generate figures
- Save reproducible artifacts

### 8.12 Skeptic Agent

Challenges everything.

Responsibilities:

- Search for prior art
- Attack novelty
- Attack feasibility
- Identify weak assumptions
- Propose rejection if needed

### 8.13 Decision Agent

Chooses next action.

Responsibilities:

- Continue
- Revise
- Pivot
- Archive
- Reject
- Promote
- Request approval

### 8.14 Skill Curator Agent

Creates and updates skills.

Responsibilities:

- Detect reusable procedures
- Create candidate skills
- Rate skill usefulness
- Update skills from feedback
- Retire weak skills

### 8.15 Archivist Agent

Documents everything.

Responsibilities:

- Maintain logs
- Generate reports
- Update idea ledger
- Update research wiki
- Save snapshots

---

## 9. Autonomy Modes

### 9.1 Strict User Mode

Used when the user gives a narrow instruction.

Behavior:

- Follow the user idea closely.
- Do not pivot.
- Research only directly relevant material.
- Report if the idea is weak.
- Suggest improvements separately.

### 9.2 Flexible User Mode

Used when the user gives a broad direction.

Behavior:

- Start from the user’s idea.
- Adapt if evidence supports a better direction.
- Log every adaptation.
- Compare original and revised ideas.

### 9.3 Full Exploration Mode

Used when the user gives broad permission.

Behavior:

- Select promising research directions independently.
- Run multiple candidate idea cycles.
- Choose strongest direction by score.

### 9.4 Idle Cognition Mode

Used when the project is active and idle.

Behavior:

- Generate or select a research idea.
- Scan recent literature.
- Detect conflicts.
- Generate questions and hypotheses.
- Score and log results.
- Continue only if value threshold is met.

---

## 10. Idle Scientific Cognition Engine

The idle engine is central to the system.

### 10.1 Idle Trigger

An idle cycle starts if:

```text
project_active = true
AND idle_research_enabled = true
AND no_research_run_active = true
AND user_inactive_time >= idle_trigger_minutes
AND daily_idle_budget_remaining = true
```

### 10.2 Idle Modes

Suggested probabilities:

```text
35% Literature frontier scan
25% Citation-conflict question generation
15% Revisit rejected idea with new literature
10% Cross-domain collision idea generation
10% Skill improvement
5% Dataset discovery
```

### 10.3 Citation-Conflict Idle Cycle

This implements the user’s example logic.

Steps:

1. Resolve subject area.
2. Generate controlled keywords and synonyms.
3. Retrieve 20 highly cited papers from the past 5 years.
4. Retrieve 20 recent frontier papers from the past 12 months.
5. Retrieve 5–10 review or survey papers.
6. Build a paper table:
   - author
   - year
   - title
   - finding
   - method
   - dataset
   - metric
   - limitation
   - citation signal
   - source
7. Cluster papers into 5–8 themes.
8. Detect conflicts inside each cluster.
9. Generate at least 10 research questions.
10. Convert top 3 questions into hypotheses.
11. Design validation steps.
12. Score each hypothesis.
13. Store accepted and rejected ideas.
14. Create or update skills.

---

## 11. Literature Intelligence Engine

### 11.1 Source Priority

Initial priority:

1. OpenAlex
2. Semantic Scholar
3. Crossref
4. arXiv
5. PubMed / Europe PMC if relevant
6. DOAJ / CORE / Unpaywall
7. Publisher APIs if allowed

### 11.2 Search Types

The engine should support:

- Keyword search
- Topic search
- Citation search
- Reference expansion
- Similar paper search
- Recent paper search
- Survey/review search
- Contradiction search
- Dataset search
- Benchmark search
- Adjacent field search

### 11.3 Paper Ranking

Rank by:

- Relevance
- Citation count
- Recency
- Field-weighted impact if available
- Venue quality
- Semantic similarity
- Whether it is a review/survey
- Whether it states limitations
- Whether it is close prior work
- Whether it challenges existing assumptions

---

## 12. Conflict and Gap Detection

Conflict categories:

```text
Finding conflict: papers report different results.
Method conflict: different methods solve the same problem.
Dataset conflict: results depend on dataset or sample.
Metric conflict: papers optimize different metrics.
Assumption conflict: papers rely on incompatible assumptions.
Scope conflict: a method works only in narrow conditions.
Theory-practice conflict: strong theory but weak deployment evidence.
Recency conflict: new work challenges older consensus.
Replication conflict: results are not reproduced across studies.
```

For each conflict, store:

```json
{
  "conflict_id": "conflict_001",
  "cluster_id": "cluster_001",
  "type": "method_conflict",
  "description": "Two method families solve the same problem but are rarely compared under identical benchmarks.",
  "supporting_papers": ["paper_001", "paper_007"],
  "opposing_papers": ["paper_012"],
  "research_opportunity": "Design a controlled benchmark comparing the methods under the same conditions."
}
```

---

## 13. Research Question and Hypothesis Generation

### 13.1 Research Question Template

Useful question forms:

```text
Why do papers using [method A] find [result X] while papers using [method B] find [result Y]?
Does [method] still work when tested under [new condition]?
Is the improvement caused by [mechanism] or by [dataset artifact]?
Can [method from adjacent field] solve [repeated limitation]?
What happens if [frontier method] is combined with [unresolved limitation]?
```

### 13.2 Hypothesis Format

Each hypothesis must include:

- Hypothesis statement
- Independent variable
- Dependent variable
- Population/context
- Expected direction
- Baseline
- Metric
- Dataset
- Failure condition

Example:

```json
{
  "hypothesis": "A cyclic research agent that alternates high-creativity ideation with low-temperature literature critique will produce higher novelty-feasibility scores than a one-shot LLM ideation baseline.",
  "independent_variable": "research workflow type",
  "dependent_variable": "expert-rated novelty-feasibility score",
  "baseline": "one-shot LLM idea generation",
  "metric": "mean expert score and prior-art overlap score",
  "failure_condition": "No statistically meaningful improvement over baseline."
}
```

---

## 14. Idea Scoring System

### 14.1 Criteria

Each idea receives scores from 0 to 10:

```text
Novelty
Feasibility
Importance
Evidence support
Validation clarity
Differentiation from prior work
Data availability
Skill leverage
User alignment
Prior-art risk
Safety risk
Cost risk
```

### 14.2 Overall Value Formula

Default:

```text
Overall Value =
0.18 × Novelty
+ 0.14 × Feasibility
+ 0.14 × Importance
+ 0.12 × Evidence Support
+ 0.14 × Validation Clarity
+ 0.12 × Differentiation
+ 0.08 × Data Availability
+ 0.05 × Skill Leverage
+ 0.03 × User Alignment
- 0.15 × Prior-Art Risk
- 0.05 × Safety Risk
- 0.03 × Cost Risk
```

### 14.3 Classification

```text
8.0–10.0 = High-value
6.5–7.9 = Promising
5.0–6.4 = Incremental or immature
3.5–4.9 = Weak
0.0–3.4 = Reject
```

The system must always explain the classification.

---

## 15. Skill Memory

The skill system is what allows the system to learn how to research.

### 15.1 Skill Types

```text
Planning skills: high-level research strategies.
Functional skills: reusable workflows like prior-art risk assessment.
Atomic skills: small tool-specific procedures.
Domain skills: field-specific research heuristics.
Evaluation skills: scoring and classification rules.
Data skills: reusable analysis scripts.
Reporting skills: templates and report structures.
Safety skills: rules for avoiding hallucination, misuse, or overclaiming.
```

### 15.2 Skill Lifecycle

```text
Candidate → Tested → Active → Revised → Deprecated → Retired
```

### 15.3 Skill Creation Triggers

Create a skill when:

- A workflow succeeds repeatedly.
- A failure reveals a reusable prevention rule.
- A user prompt creates a reusable research pattern.
- A literature-search strategy works well.
- A scoring method improves classification quality.
- A data-analysis script is reusable.
- A rejected idea teaches a general lesson.

### 15.4 Skill Evaluation

Track:

- Times used
- Success rate
- Average idea-score improvement
- Failure cases
- Last updated
- Domains where it works
- Domains where it fails

---

## 16. Knowledge Base / Research Wiki

The system should maintain a readable knowledge base.

Sections:

- Project overview
- Active research themes
- Literature maps
- Important papers
- Open conflicts
- Active hypotheses
- Rejected ideas
- Validated ideas
- Skills
- Datasets
- Reports
- Decision history

The wiki should be generated from structured data, not manually maintained.

---

## 17. Reporting System

Each completed research cycle should produce:

1. Executive summary
2. Original idea or idle trigger
3. Current refined idea
4. Flexibility/autonomy level
5. Sources searched
6. Search queries
7. Paper table
8. Paper clusters
9. Conflicts and gaps
10. Research questions
11. Hypotheses
12. Validation plan
13. Idea scores
14. Classification
15. Reason for classification
16. Decision
17. Skills used
18. Skills created or updated
19. Full audit log
20. Next recommended cycle

Export formats:

- Markdown
- HTML
- PDF
- JSON
- CSV tables
- LaTeX later

---

## 18. Safety and Governance

### 18.1 Always Allowed

- Read allowed academic sources
- Search APIs
- Summarize papers
- Generate ideas
- Score ideas
- Write reports
- Create skills
- Analyze local approved datasets
- Run code in sandbox

### 18.2 Approval Required

- Sending emails
- Publishing
- Submitting papers
- Spending money
- Accessing private accounts
- Downloading restricted datasets
- Modifying important files
- Changing safety settings
- Expanding permissions
- Using sensitive data

### 18.3 Never Allowed by Default

- Bypassing paywalls
- Scraping disallowed sites
- Fabricating citations
- Hiding failed searches
- Deleting rejection logs
- Disabling audit logs
- Treating simulated data as real
- Claiming guaranteed novelty

---

## 19. Full Development Roadmap

The project should be developed in sequential phases. Each phase has a goal, steps, deliverables, and acceptance criteria.

---

# Phase 1: Product Specification and Repository Setup

## Goal

Create a precise technical foundation for the full project.

## Steps

1. Create the main repository.
2. Define the system name, scope, and target user.
3. Create a `/docs` folder.
4. Add architecture documents.
5. Add safety policy.
6. Add data model draft.
7. Add API design draft.
8. Add development standards.
9. Choose license.
10. Set up issue templates and project board.

## Deliverables

- Repository
- Architecture document
- Safety policy
- Initial database model
- Development roadmap
- Contribution standards

## Acceptance Criteria

- Anyone can read the documentation and understand the system.
- The repository has a clear structure.
- The build plan is version-controlled.

---

# Phase 2: Core Backend Foundation

## Goal

Build the backend skeleton.

## Steps

1. Set up Python environment.
2. Install FastAPI.
3. Set up PostgreSQL.
4. Set up SQLAlchemy or SQLModel.
5. Set up Alembic migrations.
6. Create base models: Project, Idea, ResearchRun, Paper, Skill, Log.
7. Add REST API endpoints.
8. Add authentication placeholder.
9. Add configuration management.
10. Add unit test structure.

## Deliverables

- Running backend
- Database migrations
- Basic API
- Test suite skeleton

## Acceptance Criteria

- Backend starts locally.
- Database connects.
- Basic CRUD works for projects, ideas, papers, and skills.
- Tests run successfully.

---

# Phase 3: Project Manager and Settings

## Goal

Allow users to define research projects and autonomy boundaries.

## Steps

1. Create project creation API.
2. Add project domain fields.
3. Add subject scope fields.
4. Add out-of-scope fields.
5. Add source allowlist.
6. Add idle settings.
7. Add budget settings.
8. Add approval rules.
9. Add safety settings.
10. Add project settings UI later.

## Deliverables

- Project settings backend
- Project configuration schema
- Validation rules

## Acceptance Criteria

- A project can be configured with domain, sources, idle settings, and permissions.
- Invalid settings are rejected.
- Settings are included in every research run.

---

# Phase 4: Research State and Audit Log

## Goal

Make every workflow stateful and auditable.

## Steps

1. Define a ResearchState object.
2. Define run event types.
3. Log every state transition.
4. Log every tool call.
5. Log every decision.
6. Log every source query.
7. Log every idea score.
8. Add snapshot export.
9. Add run replay support later.
10. Add crash recovery foundation.

## Deliverables

- ResearchState schema
- Audit log system
- Run event timeline

## Acceptance Criteria

- A research run can be inspected step by step.
- Failed runs still preserve logs.
- The system never loses decision history.

---

# Phase 5: User Prompt Intake and Flexibility Engine

## Goal

Interpret user prompts and determine autonomy level.

## Steps

1. Build prompt intake endpoint.
2. Extract topic.
3. Extract constraints.
4. Extract output requirements.
5. Estimate flexibility.
6. Detect strict vs flexible instructions.
7. Store original prompt.
8. Generate structured intent object.
9. Add user override for flexibility.
10. Add test cases.

## Deliverables

- Prompt interpretation module
- Flexibility scoring module

## Acceptance Criteria

- Strict prompts remain strict.
- Flexible prompts allow adaptation.
- Every inferred flexibility score is explained.

---

# Phase 6: Academic Source Connectors

## Goal

Connect the system to scholarly metadata sources.

## Steps

1. Implement OpenAlex connector.
2. Implement Semantic Scholar connector.
3. Implement Crossref connector.
4. Implement arXiv connector.
5. Normalize paper metadata.
6. Deduplicate papers.
7. Store DOI, title, authors, year, abstract, venue, citations, URL.
8. Add rate-limit handling.
9. Add retry logic.
10. Add connector tests.

## Deliverables

- Academic search connectors
- Normalized paper model
- Source metadata logs

## Acceptance Criteria

- The system can search and store papers from all initial sources.
- Duplicates are merged.
- Search provenance is stored.

---

# Phase 7: Keyword Expansion and Search Planning

## Goal

Turn ideas into high-quality academic search strategies.

## Steps

1. Extract core concepts.
2. Generate synonyms.
3. Generate method terms.
4. Generate application terms.
5. Generate metric terms.
6. Generate adjacent-field terms.
7. Generate negative terms.
8. Build Boolean-like query variants.
9. Build topic-based queries when possible.
10. Store query plan.

## Deliverables

- Keyword expansion module
- Search plan object

## Acceptance Criteria

- Every idea produces a multi-query search plan.
- Search terms include adjacent terminology.
- The system can explain why each query exists.

---

# Phase 8: Literature Retrieval and Ranking

## Goal

Retrieve and rank relevant papers.

## Steps

1. Run broad search.
2. Run method-focused search.
3. Run frontier search.
4. Run review/survey search.
5. Run prior-art search.
6. Run contradiction search.
7. Merge results.
8. Rank papers.
9. Select papers for deep analysis.
10. Store selection reasons.

## Deliverables

- Retrieval pipeline
- Ranking module
- Paper selection module

## Acceptance Criteria

- The system can retrieve high-impact and recent papers.
- It can select a smaller deep-analysis set.
- Selection reasons are logged.

---

# Phase 9: Paper Analysis Engine

## Goal

Extract structured information from papers.

## Steps

1. Analyze abstracts first.
2. Retrieve full text when legally available.
3. Extract problem.
4. Extract method.
5. Extract dataset/sample.
6. Extract metrics.
7. Extract findings.
8. Extract limitations.
9. Extract future work.
10. Extract relation to current idea.

## Deliverables

- Paper analysis schema
- Paper analysis pipeline
- Evidence table

## Acceptance Criteria

- Each selected paper has structured analysis.
- Extracted facts are separated from interpretation.
- Claims are linked to source papers.

---

# Phase 10: Clustering and Literature Map

## Goal

Group papers into meaningful themes.

## Steps

1. Generate embeddings for papers.
2. Cluster by semantic similarity.
3. Cluster by method.
4. Cluster by dataset.
5. Cluster by claim/finding.
6. Label clusters.
7. Select representative papers.
8. Create cluster summaries.
9. Store cluster relationships.
10. Visualize clusters later.

## Deliverables

- Paper clusters
- Cluster labels
- Literature map

## Acceptance Criteria

- Papers are grouped into interpretable clusters.
- Each cluster has a clear theme.
- Cluster labels are justified by paper evidence.

---

# Phase 11: Conflict and Gap Detection

## Goal

Find useful research tensions.

## Steps

1. Compare findings inside clusters.
2. Compare methods inside clusters.
3. Compare datasets.
4. Compare metrics.
5. Compare assumptions.
6. Detect repeated limitations.
7. Detect missing baselines.
8. Detect weak validation patterns.
9. Detect recency conflicts.
10. Store conflicts and gaps.

## Deliverables

- Conflict list
- Gap list
- Evidence-linked opportunity map

## Acceptance Criteria

- Conflicts are categorized.
- Each conflict cites supporting papers.
- Each gap includes a possible research opportunity.

---

# Phase 12: Research Question Generator

## Goal

Derive research questions from conflicts and gaps.

## Steps

1. Generate questions from finding conflicts.
2. Generate questions from method conflicts.
3. Generate questions from dataset conflicts.
4. Generate questions from metric conflicts.
5. Generate questions from repeated limitations.
6. Remove duplicates.
7. Rank questions.
8. Link questions to source conflicts.
9. Select top questions.
10. Store rejected questions with reasons.

## Deliverables

- Research question list
- Question ranking
- Rejected question log

## Acceptance Criteria

- Every question has an evidence trail.
- Weak questions are rejected with reasons.
- Top questions are suitable for hypothesis generation.

---

# Phase 13: Hypothesis Generator

## Goal

Convert research questions into testable hypotheses.

## Steps

1. Select top research questions.
2. Define variables.
3. Define expected relationship.
4. Define context.
5. Define baseline.
6. Define metric.
7. Define data requirement.
8. Define failure condition.
9. Create hypothesis object.
10. Store version history.

## Deliverables

- Hypothesis objects
- Hypothesis versions
- Failure criteria

## Acceptance Criteria

- Every hypothesis is testable.
- Every hypothesis has failure conditions.
- Hypotheses are not vague restatements of ideas.

---

# Phase 14: Validation Planner

## Goal

Design how to test hypotheses.

## Steps

1. Search for datasets.
2. Search for benchmarks.
3. Identify baselines.
4. Recommend experimental design.
5. Recommend metrics.
6. Define sample requirements.
7. Define statistical tests if applicable.
8. Define simulation approach if real data unavailable.
9. Define expected artifacts.
10. Estimate cost and difficulty.

## Deliverables

- Validation plan
- Dataset candidates
- Baseline list
- Metric list

## Acceptance Criteria

- Every promising hypothesis has a validation plan.
- The plan includes data, baseline, metric, and failure condition.
- If validation is not feasible, the idea is downgraded.

---

# Phase 15: Idea Scoring and Classification

## Goal

Score every idea and classify it honestly.

## Steps

1. Score novelty.
2. Score feasibility.
3. Score importance.
4. Score evidence support.
5. Score validation clarity.
6. Score differentiation.
7. Score data availability.
8. Score prior-art risk.
9. Compute total value.
10. Assign classification.
11. Generate explanation.
12. Store scores and reason.

## Deliverables

- Scoring engine
- Classification engine
- Explanation generator

## Acceptance Criteria

- Every idea gets a score and classification.
- Scores are justified.
- Rejected ideas are stored, not deleted.

---

# Phase 16: Idea Ledger

## Goal

Create the permanent memory of all ideas.

## Steps

1. Build idea ledger database views.
2. Store idea versions.
3. Store origin.
4. Store score history.
5. Store classification history.
6. Store decisions.
7. Store rejection reasons.
8. Store linked papers.
9. Store linked skills.
10. Add filters and search.

## Deliverables

- Idea ledger backend
- Idea ledger UI
- Idea history view

## Acceptance Criteria

- The user can see all ideas.
- The user can see why each idea was accepted or rejected.
- The system can reuse old rejected ideas if new evidence appears.

---

# Phase 17: Idle Cognition Engine

## Goal

Allow the system to conduct autonomous background research.

## Steps

1. Implement idle detector.
2. Implement scheduler.
3. Implement idle budget manager.
4. Implement idle mode selector.
5. Implement citation-conflict idle cycle.
6. Implement frontier scan cycle.
7. Implement rejected-idea revival cycle.
8. Implement cross-domain collision cycle.
9. Implement skill-improvement cycle.
10. Log every idle run.

## Deliverables

- Idle scheduler
- Idle research workflows
- Idle run reports

## Acceptance Criteria

- The system starts idle cycles only when allowed.
- Idle cycles stay inside project scope.
- Idle cycles respect budgets.
- Every idle idea is scored and logged.

---

# Phase 18: Skill Memory System

## Goal

Make the system learn reusable research methods.

## Steps

1. Implement skill schema.
2. Implement skill storage.
3. Implement skill retrieval.
4. Implement skill creation after research runs.
5. Implement skill usage logging.
6. Implement skill scoring.
7. Implement skill versioning.
8. Implement skill retirement.
9. Implement skill browser UI.
10. Add skill tests.

## Deliverables

- Skill memory backend
- Skill lifecycle manager
- Skill browser

## Acceptance Criteria

- The system creates candidate skills.
- It retrieves relevant skills for new runs.
- It tracks whether skills help.
- Weak skills are revised or retired.

---

# Phase 19: Data Analysis Sandbox

## Goal

Allow safe, reproducible data analysis.

## Steps

1. Set up Docker execution sandbox.
2. Limit filesystem access.
3. Limit network access by policy.
4. Add dataset upload.
5. Add dataset metadata.
6. Generate analysis scripts.
7. Run scripts in sandbox.
8. Capture outputs.
9. Store figures and tables.
10. Link results to hypotheses.

## Deliverables

- Code execution sandbox
- Dataset manager
- Analysis artifacts

## Acceptance Criteria

- Code never runs directly on host.
- All analysis artifacts are saved.
- Simulated data is clearly labeled.
- Results are reproducible.

---

# Phase 20: Multi-Agent Runtime

## Goal

Formalize specialized agents and handoffs.

## Steps

1. Define agent roles.
2. Define agent instructions.
3. Define tool permissions by agent.
4. Define handoff rules.
5. Define graph workflows.
6. Add state checkpointing.
7. Add pause/resume.
8. Add approval interrupts.
9. Add failure recovery.
10. Add tracing.

## Deliverables

- Multi-agent runtime
- Agent graph definitions
- Handoff logs

## Acceptance Criteria

- Agents have clear responsibilities.
- State persists across long runs.
- A run can pause for approval and resume.
- Handoffs are logged.

---

# Phase 21: Knowledge Base and Research Wiki

## Goal

Create readable persistent knowledge.

## Steps

1. Build knowledge note schema.
2. Generate paper notes.
3. Generate cluster notes.
4. Generate conflict notes.
5. Generate hypothesis notes.
6. Generate skill notes.
7. Generate project summaries.
8. Link notes.
9. Add semantic search.
10. Add export.

## Deliverables

- Research wiki
- Semantic knowledge search
- Linked notes

## Acceptance Criteria

- The system creates a readable project knowledge base.
- Notes are linked to structured data.
- The user can search past research.

---

# Phase 22: User Dashboard

## Goal

Make the system usable by non-technical users.

## Steps

1. Build project dashboard.
2. Build active run view.
3. Build idea ledger view.
4. Build paper table view.
5. Build cluster/conflict view.
6. Build hypothesis view.
7. Build skill memory view.
8. Build idle settings view.
9. Build approval queue.
10. Build report viewer.

## Deliverables

- Web dashboard
- Research activity timeline
- Settings interface

## Acceptance Criteria

- The user can understand what the system is doing.
- The user can inspect why an idea was classified a certain way.
- The user can stop idle research.
- The user can approve or deny sensitive actions.

---

# Phase 23: Reporting and Export

## Goal

Generate complete research outputs.

## Steps

1. Build Markdown report generator.
2. Build HTML export.
3. Build PDF export.
4. Build CSV export for tables.
5. Build JSON export for machine-readable results.
6. Add report templates.
7. Add citation section.
8. Add evidence appendix.
9. Add audit appendix.
10. Add report versioning.

## Deliverables

- Research reports
- Export formats
- Versioned report archive

## Acceptance Criteria

- Every completed run produces a report.
- The report is understandable without reading logs.
- Sources, evidence, and decisions are included.

---

# Phase 24: Paper and Manuscript Support

## Goal

Support later-stage academic writing.

## Steps

1. Create paper outline from validated research.
2. Generate related work section.
3. Generate method section draft.
4. Generate experiment section draft.
5. Generate results section from analysis artifacts.
6. Generate limitations section.
7. Generate references.
8. Add LaTeX export.
9. Add manuscript review agent.
10. Add layout repair later.

## Deliverables

- Manuscript draft generator
- LaTeX export
- Review report

## Acceptance Criteria

- The system can draft a manuscript only from logged evidence.
- It clearly labels generated content.
- User approval is required before external submission.

---

# Phase 25: Evaluation and Benchmarking

## Goal

Measure whether the system actually works.

## Steps

1. Build test idea set.
2. Build baseline one-shot LLM generator.
3. Build static literature-review baseline.
4. Build cyclic agent evaluation.
5. Recruit expert evaluation later.
6. Compare novelty scores.
7. Compare feasibility scores.
8. Compare prior-art overlap.
9. Compare validation-plan quality.
10. Compare skill reuse improvement.

## Deliverables

- Evaluation suite
- Benchmark reports
- Quality metrics

## Acceptance Criteria

- The system can prove improvement over baselines.
- Skill reuse is measured.
- Idle research value is measured.

---

# Phase 26: Security, Permissions, and Compliance

## Goal

Make the full system safe and governable.

## Steps

1. Implement action allowlist.
2. Implement action blocklist.
3. Implement approval requests.
4. Implement role-based permissions.
5. Implement budget enforcement.
6. Implement source compliance checks.
7. Implement private-data warnings.
8. Implement sandbox policies.
9. Implement audit review.
10. Implement backup and restore.

## Deliverables

- Permission system
- Approval queue
- Compliance logs

## Acceptance Criteria

- No external action happens without permission.
- Restricted sources are not scraped.
- Budgets are enforced.
- Audit logs cannot be silently disabled.

---

# Phase 27: Reliability and Production Hardening

## Goal

Make the system robust.

## Steps

1. Add retry logic.
2. Add queue monitoring.
3. Add failure recovery.
4. Add run resumption.
5. Add database backups.
6. Add observability.
7. Add performance optimization.
8. Add rate-limit handling.
9. Add integration tests.
10. Add end-to-end tests.

## Deliverables

- Reliable production build
- Monitoring
- Backup strategy
- Full test suite

## Acceptance Criteria

- Long runs can survive failures.
- System can recover after restart.
- Tests cover core workflows.
- Logs make failures diagnosable.

---

# Phase 28: Packaging and Deployment

## Goal

Make the system installable and usable.

## Steps

1. Create Docker Compose setup.
2. Create local install script.
3. Create environment template.
4. Add documentation.
5. Add first-run setup wizard.
6. Add model/API key configuration.
7. Add database initialization.
8. Add example project.
9. Add sample research run.
10. Add troubleshooting guide.

## Deliverables

- Installable local package
- Docker deployment
- Setup wizard
- User documentation

## Acceptance Criteria

- A user can install locally.
- A user can create a project.
- A user can run a research cycle.
- A user can enable idle cognition.

---

# Phase 29: Final Full-System Integration

## Goal

Connect all modules into one cohesive product.

## Steps

1. Connect prompt intake to research orchestrator.
2. Connect idle engine to scheduler.
3. Connect literature engine to paper analysis.
4. Connect paper analysis to clustering.
5. Connect clustering to conflict detection.
6. Connect conflicts to questions.
7. Connect questions to hypotheses.
8. Connect hypotheses to validation planner.
9. Connect validation to scoring.
10. Connect scoring to idea ledger.
11. Connect research runs to skill memory.
12. Connect all outputs to dashboard and reports.

## Deliverables

- Fully integrated system
- Full workflow tests
- Final documentation

## Acceptance Criteria

- User-directed research works.
- Flexible adaptive research works.
- Idle autonomous research works.
- Idea scoring works.
- Skill creation and reuse works.
- Data analysis sandbox works.
- Reports and dashboard work.

---

# Phase 30: Complete Functional Release

## Goal

Release the complete version.

## Steps

1. Freeze feature set.
2. Run full regression tests.
3. Run safety tests.
4. Run benchmark tests.
5. Run documentation review.
6. Run install test on clean machine.
7. Run example project.
8. Generate release notes.
9. Tag version.
10. Publish release.

## Deliverables

- Complete functional release
- Release notes
- User guide
- Developer guide
- Example research projects

## Acceptance Criteria

The release is complete when the system can:

1. Accept a strict user idea and research it without pivoting.
2. Accept a flexible idea and improve it when justified.
3. Start idle research when allowed.
4. Retrieve scholarly literature.
5. Identify high-impact and recent papers.
6. Cluster papers.
7. Detect conflicts.
8. Generate research questions.
9. Form hypotheses.
10. Design validation plans.
11. Analyze data in a sandbox.
12. Score and classify ideas.
13. Store rejected and accepted ideas.
14. Create skills.
15. Reuse skills.
16. Produce readable reports.
17. Maintain a research wiki.
18. Show everything in a dashboard.
19. Enforce safety and permissions.
20. Preserve complete audit logs.

---

## 20. Suggested Team Structure

For a complete project, recommended roles are:

1. Product architect
2. Backend engineer
3. AI/agent engineer
4. Data engineer
5. Frontend engineer
6. Research workflow specialist
7. Scientific evaluation specialist
8. Security/reliability engineer
9. UX designer
10. Technical writer

A single strong developer can build a reduced version, but a complete full-featured system is a multi-person project.

---

## 21. Suggested Milestones

### Milestone 1: Foundation

- Backend
- Database
- Projects
- Ideas
- Logs

### Milestone 2: Academic Search

- OpenAlex
- Semantic Scholar
- Crossref
- arXiv

### Milestone 3: Literature Intelligence

- Paper analysis
- Clustering
- Conflict detection

### Milestone 4: Hypothesis and Scoring

- Research questions
- Hypotheses
- Validation plans
- Idea scoring

### Milestone 5: Idle Cognition

- Scheduler
- Idle modes
- Autonomous runs

### Milestone 6: Skill Learning

- Skill memory
- Skill creation
- Skill reuse
- Skill scoring

### Milestone 7: Data Analysis

- Sandbox
- Dataset manager
- Analysis artifacts

### Milestone 8: Dashboard

- UI
- Reports
- Idea ledger
- Skill browser

### Milestone 9: Evaluation

- Baselines
- Benchmarks
- Expert review workflow

### Milestone 10: Production Release

- Security
- Packaging
- Documentation
- Full integration

---

## 22. Final System Definition

The final product is a complete background scientific cognition system that acts like a persistent researcher’s brain. It follows strict user research requests when required, adapts flexible ideas when evidence supports a better direction, autonomously generates research questions during idle periods by analyzing recent and influential literature, detects conflicts and gaps, formulates hypotheses, validates or rejects ideas, stores all reasoning in an idea ledger, and learns reusable research skills that improve future research cycles.

---

## 23. Non-Negotiable Design Principles

1. Every idea must be logged.
2. Every rejection must have a reason.
3. Every claim must be linked to evidence where possible.
4. Every research cycle must produce an audit trail.
5. Idle autonomy must be bounded.
6. Skills must be evaluated, not blindly trusted.
7. The system must never claim guaranteed novelty.
8. User intent must control autonomy level.
9. Scientific rigor is more important than flashy output.
10. The system should become better by remembering, not by pretending to know everything.
