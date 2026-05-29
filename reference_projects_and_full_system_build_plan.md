# Reference Projects and Full-System Build Plan

## Project: Background Scientific Cognition System

This document consolidates the reference-project analysis and the full build strategy into one implementation plan.

The purpose is to explain which external GitHub projects should be used as references, which parts of them are useful, what should not be copied, and how their ideas should be combined into a complete production-grade system.

This is not an MVP plan. It is a complete-system plan.

---

## 1. Executive Summary

The project we want to build is a **background scientific cognition system**: a long-running autonomous research platform that behaves like a persistent researcher’s brain.

It should:

1. Accept user research ideas.
2. Detect whether the user wants strict execution or flexible adaptation.
3. Follow strict prompts exactly when required.
4. Adapt flexible ideas when evidence supports a better research direction.
5. Initiate idle research when the project is active but no task is running.
6. Monitor recent scientific literature.
7. Retrieve high-impact papers, frontier papers, review papers, and contradictory papers.
8. Cluster literature into themes.
9. Detect conflicts, gaps, repeated limitations, and weak assumptions.
10. Generate research questions from those conflicts.
11. Convert research questions into testable hypotheses.
12. Design validation plans.
13. Analyze data or run simulations when appropriate.
14. Score and classify every idea.
15. Store valuable and worthless ideas with reasons.
16. Create reusable research skills from successful and failed cycles.
17. Use those skills in future research.
18. Maintain a full audit trail.
19. Provide a dashboard, reports, and a persistent research wiki.
20. Remain bounded by safety, permissions, source compliance, and cost controls.

The central product idea is:

```text
A self-learning background scientific cognition system that continuously watches the literature, detects conflicts and gaps, generates research questions, forms hypotheses, validates or rejects ideas, and turns research experience into reusable skills.
```

---

## 2. Final System Identity

This project should not be positioned merely as an “AI research assistant.” Many existing projects already do literature review, paper writing, or experiment automation.

The stronger identity is:

```text
A researcher-like cognitive operating system for scientific idea discovery.
```

It has five distinctive properties:

1. **User-flexibility-aware autonomy**  
   The system changes behavior depending on whether the user gives a strict prompt, a flexible idea, or no idea at all.

2. **Idle scientific cognition**  
   When active but idle, it autonomously scans literature and generates new research questions.

3. **Conflict-driven question generation**  
   It does not generate random ideas blindly. It identifies conflicts, gaps, and unresolved tensions in the literature.

4. **Idea ledger with rejection memory**  
   It stores all ideas, including bad ones, with scores and rejection reasons.

5. **Skill memory**  
   It learns reusable research procedures from previous cycles and applies them to future work.

---

## 3. Reference Project Strategy

The system should not simply fork one repository and modify it.

The correct strategy is:

```text
Use one project as the conceptual anchor,
use another as the engineering reference,
and selectively borrow mechanisms from the rest.
```

Recommended reference structure:

| Role | Reference Project | How to Use It |
|---|---|---|
| Primary conceptual reference | ScienceClaw | Research memory, scientific skills, citation discipline, self-evolving colleague concept |
| Primary engineering reference | DeerFlow | Long-horizon orchestration, subagents, tools, sandboxes, memory, message gateway |
| Research lifecycle reference | freephdlabor | Multi-agent scientific lifecycle, hypothesis to experiment to manuscript |
| Research workflow reference | Agent Laboratory | Literature review → experimentation → report-writing phases |
| Automated discovery precedent | AI-Scientist | Open-ended scientific discovery benchmark and conceptual prior art |
| Skill-learning reference | SkillX | Planning / functional / atomic skill hierarchy |
| Idle creativity reference | Open Collider | Cross-domain semantic collision for non-trivial idea generation |
| Knowledge-base reference | WeKnora | RAG, autonomous reasoning, self-maintaining wiki |
| Structured research-state reference | PhysicsIntern | Explicit research state, critique, reproducibility, scientific problem solving |
| Academic workflow reference | Claude Scholar | Semi-automated research workflow, project organization, evidence pipeline |
| Research skill-pack reference | academic-research-skills | Research → write → review → revise → finalize skill patterns |
| Paper-writing reference | PaperOrchestra | Multi-agent paper drafting, literature review, plotting, refinement |
| Writing workspace reference | Claude Prism | Offline-first scientific writing workspace and local scientific skills |
| Manuscript review/editing reference | PaperDebugger | In-editor academic writing, review, and editing |
| Layout/LaTeX reference | PaperFit | Vision-in-the-loop LaTeX layout repair |
| Formal math validation reference | MathCode | Math formalization and proof-related tooling |
| Codebase understanding reference | CodeGraph | Local code graph for repository analysis |
| Writing polish reference | stop-slop | Remove generic AI prose patterns; minor reporting polish only |
| Avoid | humanize-text | Not aligned with transparent research; do not use |
| Landscape monitoring | Awesome-Deep-Research | Watch new deep-research systems and papers |

---

## 4. Reference Project Analysis

This section explains each repository, what it contributes, what should be reused conceptually, what should not be copied, and where it fits into the build.

---

### 4.1 ScienceClaw

Repository: https://github.com/beita6969/ScienceClaw

#### What it is

ScienceClaw presents itself as a self-evolving AI research colleague for scientists, with persistent memory, scientific skills, and citation-grounded behavior.

#### Why it matters

This is the closest conceptual reference to our project. It already points toward a research companion that remembers, adapts, and develops skills.

#### What to use

Use ScienceClaw as the reference for:

- Persistent research memory.
- Scientific skill files.
- Self-evolving skill concept.
- Long-duration research behavior.
- Domain adaptation.
- Anti-hallucination behavior.
- Citation discipline.
- Research-specific workflows rather than generic agent behavior.

#### What not to copy blindly

Do not copy the whole architecture as-is.

Our system needs additional elements that should be central:

- User-flexibility-aware autonomy.
- Idle scientific cognition.
- Conflict-to-question generation.
- Idea scoring.
- Explicit worthless/valuable classification.
- Rejection memory.
- Skill evaluation and retirement.
- Research question and hypothesis ledger.

#### How to integrate the idea

ScienceClaw should inspire our **Skill Memory**, **Research Memory**, and **Research Protocol** modules.

Implementation mapping:

```text
ScienceClaw inspiration
→ Research Memory Store
→ Skill Memory Store
→ Citation-Discipline Guardrails
→ Long-Run Research Protocols
→ Domain-Adaptive Skill Retrieval
```

---

### 4.2 DeerFlow

Repository: https://github.com/bytedance/deer-flow

#### What it is

DeerFlow is a long-horizon super-agent harness with subagents, memory, tools, skills, sandboxes, and a message gateway.

#### Why it matters

Our system needs long-running workflows that may last minutes or hours, may pause for approval, may resume after failure, and may coordinate many specialized agents.

DeerFlow is useful as an engineering reference for that runtime model.

#### What to use

Use DeerFlow as reference for:

- Long-horizon task orchestration.
- Subagent coordination.
- Tool gateway design.
- Sandbox integration.
- Message/event gateway.
- Memory integration.
- Skill execution model.
- Task runtime structure.

#### What not to copy blindly

DeerFlow is general-purpose. Our system is research-specific.

Do not let the project become a generic agent harness. The core product must remain scientific cognition:

```text
literature → conflict → question → hypothesis → validation → score → memory → skill
```

#### How to integrate the idea

Use DeerFlow-style architecture for the **Multi-Agent Runtime** and **Tool Gateway**.

Implementation mapping:

```text
DeerFlow inspiration
→ Research Orchestrator
→ Agent Runtime
→ Tool Gateway
→ Sandbox Manager
→ Memory Bridge
→ Message Bus
```

---

### 4.3 freephdlabor

Repository: https://github.com/ltjed/freephdlabor

#### What it is

freephdlabor is a multi-agent framework that aims to automate the scientific research lifecycle from hypothesis generation through experimentation to publication-ready manuscripts.

#### Why it matters

This is one of the closest end-to-end research-lifecycle references.

It demonstrates the idea that specialized agents can coordinate around scientific tasks.

#### What to use

Use freephdlabor as reference for:

- Multi-agent research workflow.
- Manager agent pattern.
- Ideation agent.
- Experimentation agent.
- Writeup agent.
- Review agent.
- Proofreading agent.
- Workspace-based collaboration.
- Domain-specific customization.
- Resume/interruption behavior.

#### What not to copy blindly

Do not make the first system goal “wake up to a paper.”

Our system should first produce:

- Literature map.
- Conflict map.
- Research questions.
- Hypotheses.
- Validation plans.
- Idea scores.
- Rejection reasons.
- Skills.

Paper generation is a later stage.

#### How to integrate the idea

freephdlabor should inspire the **Research Lifecycle Agents**.

Implementation mapping:

```text
freephdlabor ManagerAgent
→ Our Research Orchestrator

freephdlabor IdeationAgent
→ Our Idle Cognition Agent + Research Question Agent

freephdlabor ExperimentationAgent
→ Our Validation Planner + Data Analysis Sandbox

freephdlabor WriteupAgent
→ Our Report Generator + Manuscript Support

freephdlabor ReviewerAgent
→ Our Skeptic Agent + Evaluation Agent
```

---

### 4.4 Agent Laboratory

Repository: https://github.com/SamuelSchmidgall/AgentLaboratory

#### What it is

Agent Laboratory is an autonomous research workflow designed to assist human researchers in implementing research ideas. It is structured around literature review, experimentation, and report writing.

#### Why it matters

It provides a clean research workflow structure that maps well to our early core pipeline.

#### What to use

Use it as reference for:

- Literature review phase.
- Experimentation phase.
- Report-writing phase.
- Tool-based research workflow.
- Human researcher assistive framing.
- arXiv and code-based experimentation patterns.

#### What not to copy blindly

Agent Laboratory is more user-idea-driven and assistive.

Our system should go beyond that by adding:

- Idle autonomous idea discovery.
- Conflict-driven question generation.
- Idea ledger.
- Worthless idea classification.
- Skill creation.
- Long-term memory.

#### How to integrate the idea

Use Agent Laboratory as the reference for the basic sequence:

```text
Literature Review → Experimentation → Report
```

Then extend it into:

```text
Literature Review → Conflict Detection → Research Questions → Hypotheses → Validation → Scoring → Skill Creation → Report
```

---

### 4.5 AI-Scientist

Repository: https://github.com/SakanaAI/AI-Scientist

#### What it is

AI-Scientist is a system for open-ended scientific discovery using AI agents.

#### Why it matters

It is important prior art. It validates that autonomous scientific discovery is an active research direction.

#### What to use

Use it as reference for:

- End-to-end scientific discovery ambition.
- Idea generation.
- Experiment execution.
- Scientific paper generation.
- Automated review patterns.
- Benchmarking against existing autonomous-science systems.

#### What not to copy blindly

Do not use it as the main base.

Reasons:

- Our project’s differentiator is not just automated discovery.
- Our system is memory-heavy, skill-learning-heavy, and idle-cognition-heavy.
- Licensing and responsible-use conditions must be reviewed before reuse.
- Our system should not imply full scientific novelty proof.

#### How to integrate the idea

Use AI-Scientist as a **benchmark and prior-art comparison**, not as the core architecture.

Implementation mapping:

```text
AI-Scientist inspiration
→ Automated Discovery Benchmark
→ Experiment Automation Reference
→ Reviewer-Agent Reference
→ Scientific Output Baseline
```

---

### 4.6 SkillX

Repository: https://github.com/zjunlp/SkillX

#### What it is

SkillX focuses on automatically constructing skill knowledge bases for agents.

#### Why it matters

Our system must learn how to research. SkillX is directly relevant to the Skill Memory layer.

#### What to use

Use SkillX as reference for:

- Skill extraction from agent experience.
- Skill hierarchy.
- Planning skills.
- Functional skills.
- Atomic skills.
- Skill knowledge base construction.
- Skill reuse.

#### How to adapt it

Our skill hierarchy should be:

```text
Planning Skills
High-level research strategies.
Example: Citation-Conflict Research Question Generation.

Functional Skills
Reusable multi-step workflows.
Example: Prior-Art Risk Assessment.

Atomic Skills
Small tool-specific procedures.
Example: Query OpenAlex for top-cited papers from the last 5 years.
```

#### What not to copy blindly

SkillX is general agent skill construction. Our system needs scientific-skill evaluation.

Every skill should have:

- Trigger conditions.
- Inputs.
- Procedure.
- Outputs.
- Success metrics.
- Failure history.
- Version.
- Status.
- Domains where it works.
- Domains where it fails.

#### How to integrate the idea

SkillX should directly inspire the **Skill Memory System**.

Implementation mapping:

```text
SkillX hierarchy
→ Research Skill Taxonomy
→ Skill Extraction Agent
→ Skill Retrieval Engine
→ Skill Evaluation Engine
→ Skill Lifecycle Manager
```

---

### 4.7 Open Collider

Repository: https://github.com/CL-ML/open-collider

#### What it is

Open Collider is a semantic collision engine for non-trivial LLM idea generation. It uses structurally distant domains to generate less obvious ideas.

#### Why it matters

Idle research must not be shallow random ideation. It should produce non-trivial ideas by combining distant but meaningful concepts.

#### What to use

Use Open Collider as reference for:

- Cross-domain idea generation.
- Semantic collision.
- Distant-domain transfer.
- Creativity mode.
- Non-obvious hypothesis generation.

#### What not to copy blindly

Open Collider is not a full research system.

It should be one idle-cognition mode, not the entire project.

#### How to integrate the idea

Add it as one mode in Idle Cognition:

```text
Idle Mode: Cross-Domain Collision
1. Select current research cluster.
2. Select a structurally distant field.
3. Extract mechanism from distant field.
4. Transfer mechanism into current field.
5. Generate candidate idea.
6. Search literature for prior art.
7. Score novelty and feasibility.
```

Suggested idle-mode probability:

```text
10% Cross-domain collision idea generation
```

---

### 4.8 WeKnora

Repository: https://github.com/Tencent/WeKnora

#### What it is

WeKnora is an LLM knowledge platform that turns raw documents into queryable RAG, autonomous reasoning, and a self-maintaining wiki.

#### Why it matters

Our system needs a living knowledge base: papers, notes, hypotheses, skills, conflicts, and reports must be searchable and readable.

#### What to use

Use WeKnora as reference for:

- RAG over research documents.
- Self-maintaining wiki.
- Knowledge graph.
- Document ingestion.
- Semantic retrieval.
- Autonomous reasoning over stored knowledge.

#### What not to copy blindly

WeKnora is a knowledge platform, not a research-brain pipeline.

Do not make retrieval the final product. Retrieval supports cognition; it is not cognition by itself.

#### How to integrate the idea

Use WeKnora-style components for the **Knowledge Base and Research Wiki**.

Implementation mapping:

```text
WeKnora inspiration
→ Research Wiki
→ Paper Knowledge Base
→ Semantic Retrieval
→ Literature Memory
→ Skill Search
→ Idea History Search
```

---

### 4.9 PhysicsIntern

Repository: https://github.com/huggingface/physics-intern

#### What it is

PhysicsIntern is an agentic framework for solving scientific research problems, especially in physics and mathematics.

#### Why it matters

It is valuable because it emphasizes structured scientific state, decomposition, verification, review, critique, and reproducibility.

#### What to use

Use PhysicsIntern as reference for:

- Structured ResearchState object.
- Scientific problem decomposition.
- Reviewer and critic roles.
- Verification mindset.
- Snapshotting.
- Reproducible state.
- Scientific reasoning pipelines.

#### What not to copy blindly

PhysicsIntern is domain-specific.

Our system must generalize across fields and emphasize literature-driven idea discovery.

#### How to integrate the idea

Use the structured-state principle everywhere.

Implementation mapping:

```text
PhysicsIntern inspiration
→ ResearchState Object
→ Run Snapshots
→ Critic Agent
→ Reviewer Agent
→ Reproducibility Logs
```

---

### 4.10 Claude Scholar

Repository: https://github.com/Galaxy-Dawn/claude-scholar

#### What it is

Claude Scholar is a semi-automated research assistant for academic research and software development, covering ideation, coding, experiments, writing, and publication support.

#### Why it matters

It is useful for organizing academic workflows, especially where human decision-making remains central.

#### What to use

Use it as reference for:

- Project organization.
- Human-readable research workflow.
- Literature and note workflows.
- Evidence pipeline.
- Research-to-writing continuity.
- Integration with coding and publication workflows.

#### What not to copy blindly

It is deliberately semi-automated.

Our system should support human control but also include autonomous idle cognition.

#### How to integrate the idea

Use Claude Scholar as a reference for UX and researcher-facing workflows.

Implementation mapping:

```text
Claude Scholar inspiration
→ Research Project Workspace
→ Human Review Layer
→ Writing Workflow
→ Evidence Organization
```

---

### 4.11 academic-research-skills

Repository: https://github.com/Imbad0202/academic-research-skills

#### What it is

A collection of academic research skills for Claude Code: research, write, review, revise, finalize.

#### Why it matters

It provides reusable skill patterns for academic work.

#### What to use

Use it as reference for:

- Academic skill file format.
- Research workflow skills.
- Review and revision skills.
- Finalization procedures.
- Quality-control checklists.

#### What not to copy blindly

It is a skill pack, not a full autonomous system.

#### How to integrate the idea

Use it as a seed reference for our **Reporting Skills**, **Review Skills**, and **Revision Skills**.

---

### 4.12 PaperOrchestra

Repository: https://github.com/Ar9av/PaperOrchestra

#### What it is

PaperOrchestra is a skill-based implementation of a multi-agent pipeline for automated research-paper writing, including outline, plotting, literature review, section writing, and content refinement.

#### Why it matters

Our system will eventually need to turn validated research into reports and manuscripts.

#### What to use

Use PaperOrchestra as reference for:

- Paper outline generation.
- Plotting plan.
- Literature-review drafting.
- Section writing.
- Content refinement.
- Paper-quality autoraters.
- Deterministic validation helpers.
- Agent-log aggregation.

#### What not to copy blindly

Do not make paper writing the primary system goal.

Paper writing should only occur after:

- Research question is supported.
- Hypothesis is clear.
- Evidence exists.
- Validation is complete or planned.
- Idea score is high enough.

#### How to integrate the idea

Use it in the **Manuscript Support** phase.

Implementation mapping:

```text
PaperOrchestra inspiration
→ Research Report Generator
→ Manuscript Drafting Agent
→ Literature Review Drafting
→ Figure/Plot Planning
→ Content Refinement Agent
→ Autorater Evaluation
```

---

### 4.13 Claude Prism

Repository: https://github.com/delibae/claude-prism

#### What it is

Claude Prism is an offline-first scientific writing workspace with LaTeX, Python, and scientific skills.

#### Why it matters

The final system may need a local scientific writing workspace.

#### What to use

Use it as reference for:

- Offline-first writing workspace.
- Local scientific skills.
- LaTeX + Python integration.
- Scientific drafting environment.

#### What not to copy blindly

It is more writing-oriented than research-cognition-oriented.

#### How to integrate the idea

Use it as a reference for the **Writing Workspace** and **Local Scientific Workspace**.

---

### 4.14 PaperDebugger

Repository: https://github.com/PaperDebugger/paperdebugger

#### What it is

PaperDebugger is a plugin-based multi-agent system for in-editor academic writing, review, and editing.

#### Why it matters

It is useful for the manuscript editing stage.

#### What to use

Use it as reference for:

- In-editor paper review.
- Academic editing agents.
- Plugin-based review tools.
- Manuscript debugging.

#### What not to copy blindly

It is not a discovery engine.

#### How to integrate the idea

Use it later for **Manuscript Review and Editing**.

---

### 4.15 PaperFit

Repository: https://github.com/OpenRaiser/PaperFit

#### What it is

PaperFit is a vision-in-the-loop LaTeX typesetting agent that compiles, renders, diagnoses, and fixes paper layouts.

#### Why it matters

Useful only at the final publication/layout stage.

#### What to use

Use it as reference for:

- PDF render-check loop.
- LaTeX layout diagnosis.
- Visual feedback for formatting.
- Acceptance gate for paper layout.

#### What not to copy blindly

Do not use this before the research system itself works.

#### How to integrate the idea

Use it in the final **Publication Formatting** phase.

---

### 4.16 MathCode

Repository: https://github.com/math-ai-org/mathcode

#### What it is

MathCode is a mathematical coding agent with formalization capabilities.

#### Why it matters

Some research fields need formal mathematical verification.

#### What to use

Use it as reference for:

- Math formalization.
- Lean-style theorem statements.
- Formal proof attempts.
- Math-heavy validation workflows.

#### What not to copy blindly

It is not a general research-brain architecture.

#### How to integrate the idea

Use it as an optional **Formal Validation Tool** for math-heavy projects.

---

### 4.17 CodeGraph

Repository: https://github.com/colbymchenry/codegraph

#### What it is

CodeGraph is a local code knowledge graph for AI coding agents.

#### Why it matters

Our system may need to analyze codebases, reproduce experiments, inspect repositories, or understand its own project structure.

#### What to use

Use it as reference for:

- Local repository indexing.
- Symbol graph.
- Codebase query.
- Reduced token usage during code analysis.
- Experiment-code understanding.

#### What not to copy blindly

It is not an academic research system.

#### How to integrate the idea

Use it in the **Code Understanding** and **Experiment Reproduction** layer.

---

### 4.18 stop-slop

Repository: https://github.com/hardikpandya/stop-slop

#### What it is

A skill file for removing common AI tells from prose.

#### Why it matters

It may be useful for improving report quality and reducing generic AI phrasing.

#### What to use

Use it only for:

- Report polish.
- Reducing generic prose.
- Making writing clearer and less formulaic.

#### What not to copy blindly

Do not use it to disguise AI authorship.

The system should remain transparent and auditable.

#### How to integrate the idea

Use as a minor **Writing Quality Skill**.

---

### 4.19 humanize-text

Repository: https://github.com/lynote-ai/humanize-text

#### What it is

A project positioned around making AI text undetectable and bypassing AI detectors.

#### Why it should be avoided

This is not aligned with scientific transparency.

Our system should be:

- Auditable.
- Citation-grounded.
- Transparent about generated content.
- Honest about evidence and uncertainty.

#### Decision

Do not use this project.

---

### 4.20 Awesome-Deep-Research

Repository: https://github.com/DavidZWZ/Awesome-Deep-Research

#### What it is

A curated list of deep-research resources.

#### Why it matters

It is useful for landscape monitoring.

#### What to use

Use it for:

- Finding new deep-research systems.
- Tracking papers.
- Tracking benchmarks.
- Competitive analysis.

#### What not to copy blindly

It is a resource list, not a product or architecture.

#### How to integrate the idea

Use as a monitored source in the **Landscape Monitoring Skill**.

---

## 5. Final System Architecture

The final system should consist of the following major modules.

### 5.1 User Interface

Purpose:

Allow the user to create projects, submit ideas, inspect active research runs, view idea ratings, review reports, inspect skills, approve sensitive actions, and configure idle cognition.

Reference influence:

- Claude Scholar for researcher-facing workflow.
- Claude Prism for scientific workspace.
- PaperDebugger for in-editor review ideas.

Core screens:

1. Project dashboard.
2. Active research run timeline.
3. Idea ledger.
4. Idea detail page.
5. Literature table.
6. Cluster/conflict map.
7. Research questions.
8. Hypotheses.
9. Validation plans.
10. Skill memory.
11. Research wiki.
12. Reports.
13. Approval queue.
14. Settings.

---

### 5.2 Project Manager

Purpose:

Store each project’s domain, scope, autonomy rules, allowed sources, idle settings, budgets, and safety restrictions.

Reference influence:

- ScienceClaw for domain adaptation.
- Claude Scholar for project organization.

Core fields:

```json
{
  "project_name": "Autonomous Scientific Research Brain",
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
  "max_sources_per_cycle": 50
}
```

---

### 5.3 Research Orchestrator

Purpose:

Coordinate all agents, workflows, budgets, states, and approvals.

Reference influence:

- DeerFlow for long-horizon orchestration.
- freephdlabor for ManagerAgent pattern.
- PhysicsIntern for structured state.

Core duties:

1. Start research runs.
2. Resume paused runs.
3. Assign tasks to agents.
4. Enforce budgets.
5. Route tool calls.
6. Pause for approval.
7. Log every state transition.
8. Generate final reports.

---

### 5.4 Autonomy and Flexibility Engine

Purpose:

Determine how much freedom the system has.

Modes:

```text
0.0 = strict execution
0.25 = minor refinement allowed
0.50 = adjacent pivot allowed
0.75 = major reframing allowed if justified
1.0 = agent chooses best direction independently
```

Behavior:

```text
Strict user prompt:
    Follow directly.

Flexible user prompt:
    Start from prompt, adapt if evidence supports it.

No prompt + idle enabled:
    Start background scientific cognition cycle.
```

Reference influence:

This is mostly our own differentiator. Existing projects do not fully center this mechanism.

---

### 5.5 Idle Cognition Engine

Purpose:

Let the system think like a researcher during idle moments.

Reference influence:

- Open Collider for cross-domain idea generation.
- ScienceClaw for persistent research memory.
- freephdlabor for 24/7 research ambition.
- Awesome-Deep-Research for landscape monitoring.

Idle trigger:

```text
project_active = true
idle_research_enabled = true
no_active_research_run = true
user_inactive_time >= threshold
daily_idle_budget_remaining = true
```

Idle modes:

```text
35% Literature frontier scan
25% Citation-conflict question generation
15% Revisit rejected ideas with new literature
10% Cross-domain collision idea generation
10% Skill improvement
5% Dataset discovery
```

---

### 5.6 Literature Intelligence Engine

Purpose:

Search, retrieve, rank, and analyze academic literature.

Reference influence:

- Agent Laboratory for literature review phase.
- ScienceClaw for citation discipline.
- Claude Scholar for academic organization.

Initial data sources:

1. OpenAlex.
2. Semantic Scholar.
3. Crossref.
4. arXiv.
5. PubMed / Europe PMC when relevant.
6. DOAJ / CORE / Unpaywall.
7. Publisher APIs only when allowed.

Search types:

- High-impact papers from last 5 years.
- Frontier papers from last 6–12 months.
- Review/survey papers.
- Contradictory papers.
- Dataset papers.
- Benchmark papers.
- Adjacent-field papers.

---

### 5.7 Paper Ingestion and Parsing Engine

Purpose:

Normalize metadata and extract structured information from papers.

Inputs:

- Title.
- Authors.
- Year.
- Abstract.
- DOI.
- Venue.
- URL.
- Citation count.
- References.
- Full text when legally available.

Extracted fields:

- Problem.
- Method.
- Dataset.
- Metric.
- Finding.
- Limitation.
- Future work.
- Assumption.
- Relation to current idea.

Reference influence:

- ScienceClaw for evidence-grounded extraction.
- Agent Laboratory for literature workflow.
- PaperOrchestra for literature-review structuring.

---

### 5.8 Paper Clustering Engine

Purpose:

Group papers into themes.

Cluster types:

- Topic cluster.
- Method cluster.
- Dataset cluster.
- Metric cluster.
- Claim/finding cluster.
- Application cluster.

Reference influence:

- Our own latest discussion on clustering top papers into themes.
- WeKnora for semantic knowledge organization.

---

### 5.9 Conflict and Gap Detection Engine

Purpose:

Detect scientific tensions that can generate research questions.

Conflict categories:

```text
Finding conflict
Method conflict
Dataset conflict
Metric conflict
Assumption conflict
Scope conflict
Theory-practice conflict
Recency conflict
Replication conflict
```

Each conflict should include:

- Conflict type.
- Description.
- Supporting papers.
- Opposing papers.
- Why it matters.
- Possible research opportunity.

This is one of our most important differentiators.

---

### 5.10 Research Question Generator

Purpose:

Generate research questions from conflicts, gaps, and repeated limitations.

Question templates:

```text
Why do papers using [method A] find [result X] while papers using [method B] find [result Y]?

Does [method] still work under [new condition]?

Is the improvement caused by [mechanism] or by [dataset artifact]?

Can [method from adjacent field] solve [repeated limitation]?

What happens if [frontier method] is combined with [unresolved limitation]?
```

Reference influence:

- Open Collider for creative transfer.
- Literature-conflict logic from our design.

---

### 5.11 Hypothesis Generator

Purpose:

Convert questions into testable hypotheses.

Each hypothesis must include:

- Statement.
- Independent variable.
- Dependent variable.
- Context.
- Baseline.
- Dataset.
- Metric.
- Expected direction.
- Failure condition.

Reference influence:

- freephdlabor for hypothesis-to-experiment flow.
- Agent Laboratory for experiment planning.
- AI-Scientist for autonomous discovery framing.

---

### 5.12 Validation Planner

Purpose:

Design how to test each hypothesis.

Outputs:

- Dataset candidates.
- Benchmark candidates.
- Baselines.
- Metrics.
- Experimental design.
- Statistical tests.
- Simulation option.
- Expected artifacts.
- Difficulty estimate.
- Cost estimate.

Reference influence:

- freephdlabor ExperimentationAgent.
- Agent Laboratory experimentation phase.
- PhysicsIntern verification mindset.

---

### 5.13 Data Analysis Sandbox

Purpose:

Run safe, reproducible code and analysis.

Reference influence:

- DeerFlow for sandboxes.
- freephdlabor for experiment execution.
- PhysicsIntern for reproducibility.
- MathCode for formal validation in math-heavy domains.

Rules:

1. Never execute analysis directly on the host system.
2. Use Docker or another sandbox.
3. Preserve scripts.
4. Preserve outputs.
5. Label simulated data clearly.
6. Link results to hypotheses.

---

### 5.14 Idea Scoring Engine

Purpose:

Rate each idea and decide whether it is valuable, promising, weak, or reject.

Scores:

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

Classification:

```text
8.0–10.0 = High-value
6.5–7.9 = Promising
5.0–6.4 = Incremental or immature
3.5–4.9 = Weak
0.0–3.4 = Reject
```

This is a core differentiator. Most reference projects do not make rejected ideas and rejection reasons central.

---

### 5.15 Idea Ledger

Purpose:

Store every idea forever, including bad ideas.

Each idea record should include:

- Idea ID.
- Origin.
- User prompt if any.
- Flexibility level.
- Initial idea.
- Current revised idea.
- Versions.
- Keywords.
- Papers searched.
- Clusters.
- Conflicts.
- Research questions.
- Hypotheses.
- Validation plans.
- Scores.
- Classification.
- Rejection or continuation reason.
- Related skills.
- Reports.

Reference influence:

This is mostly our original architecture. It should be treated as a central product feature.

---

### 5.16 Skill Memory System

Purpose:

Convert research experience into reusable research skills.

Reference influence:

- ScienceClaw for self-evolving skills.
- SkillX for skill hierarchy.
- academic-research-skills for skill-pack structure.
- PaperOrchestra for skill documents and deterministic helpers.

Skill hierarchy:

```text
Planning Skill:
High-level research strategy.
Example: Citation-Conflict Research Question Generator.

Functional Skill:
Reusable multi-step workflow.
Example: Prior-Art Risk Assessment.

Atomic Skill:
Small tool-use procedure.
Example: Query OpenAlex for recent high-impact papers.
```

Skill lifecycle:

```text
Candidate → Tested → Active → Revised → Deprecated → Retired
```

Skill creation triggers:

- A workflow succeeds repeatedly.
- A failure reveals a reusable prevention rule.
- A search strategy works well.
- A scoring method improves idea classification.
- A user preference repeats.
- A data-analysis script is reusable.

---

### 5.17 Knowledge Base and Research Wiki

Purpose:

Maintain a readable project memory.

Reference influence:

- WeKnora for self-maintaining wiki.
- Claude Scholar for academic organization.
- ScienceClaw for persistent research memory.

Sections:

- Project overview.
- Literature maps.
- Important papers.
- Open conflicts.
- Research questions.
- Active hypotheses.
- Rejected ideas.
- Validated ideas.
- Skills.
- Datasets.
- Reports.
- Decision history.

---

### 5.18 Reporting and Manuscript Support

Purpose:

Generate research reports and later manuscript drafts.

Reference influence:

- PaperOrchestra for paper pipeline.
- Claude Prism for writing workspace.
- PaperDebugger for review/editing.
- PaperFit for LaTeX layout.
- stop-slop for minor prose cleanup.

Report sections:

1. Executive summary.
2. Original idea.
3. Revised idea.
4. Autonomy/flexibility level.
5. Sources searched.
6. Search queries.
7. Paper table.
8. Clusters.
9. Conflicts.
10. Research questions.
11. Hypotheses.
12. Validation plan.
13. Scores.
14. Classification.
15. Decision.
16. Skills used.
17. Skills created.
18. Audit log.
19. Next cycle.

---

## 6. Build Strategy

The final system should be built in phases. Each phase should produce a usable layer of the final architecture.

---

## Phase 1: Repository and Product Specification

### Goal

Create the project foundation.

### Steps

1. Create the main repository.
2. Create `/docs` folder.
3. Add project vision document.
4. Add architecture document.
5. Add reference-project document.
6. Add safety policy.
7. Add data model draft.
8. Add roadmap.
9. Add issue templates.
10. Add project board.

### Deliverables

- Repository.
- Documentation skeleton.
- Architecture overview.
- Reference project plan.

### Acceptance Criteria

- A new contributor can understand the project from documentation alone.
- The project’s difference from ScienceClaw, freephdlabor, AI-Scientist, and Agent Laboratory is clear.

---

## Phase 2: Backend Foundation

### Goal

Build the backend and database core.

### Steps

1. Set up Python backend.
2. Set up FastAPI.
3. Set up PostgreSQL.
4. Set up migrations.
5. Create core models.
6. Add REST APIs.
7. Add configuration management.
8. Add logging.
9. Add tests.
10. Add Docker Compose.

### Core models

```text
Project
Idea
ResearchRun
Paper
PaperAnalysis
Cluster
Conflict
ResearchQuestion
Hypothesis
ValidationPlan
Skill
Report
AuditLog
```

### Reference influence

- DeerFlow for long-running architecture.
- PhysicsIntern for state-first design.

---

## Phase 3: Project Manager and Autonomy Settings

### Goal

Allow projects to define domains, scopes, autonomy, idle rules, and safety boundaries.

### Steps

1. Build project creation.
2. Build domain/scope fields.
3. Build out-of-scope fields.
4. Build default flexibility settings.
5. Build idle settings.
6. Build source allowlist.
7. Build budget settings.
8. Build approval settings.
9. Add validation.
10. Add tests.

### Reference influence

- ScienceClaw for domain adaptation.
- Claude Scholar for project organization.

---

## Phase 4: Research State and Audit Log

### Goal

Make every run inspectable and recoverable.

### Steps

1. Define ResearchState schema.
2. Store state snapshots.
3. Store tool calls.
4. Store decisions.
5. Store sources.
6. Store score changes.
7. Store errors.
8. Build run timeline API.
9. Add replay support later.
10. Add failure recovery.

### Reference influence

- PhysicsIntern for structured state.
- DeerFlow for long-horizon task tracking.

---

## Phase 5: Academic Search Connectors

### Goal

Connect to structured scholarly sources.

### Steps

1. Implement OpenAlex connector.
2. Implement Semantic Scholar connector.
3. Implement Crossref connector.
4. Implement arXiv connector.
5. Implement PubMed/Europe PMC optional connector.
6. Normalize metadata.
7. Deduplicate papers.
8. Store provenance.
9. Handle rate limits.
10. Add connector tests.

### Reference influence

- Agent Laboratory for literature search workflow.
- ScienceClaw for citation discipline.

---

## Phase 6: Keyword Expansion and Search Planning

### Goal

Turn ideas into high-quality academic search plans.

### Steps

1. Extract core terms.
2. Generate synonyms.
3. Generate method terms.
4. Generate application terms.
5. Generate metric terms.
6. Generate adjacent-field terms.
7. Generate negative terms.
8. Generate high-impact query.
9. Generate frontier query.
10. Generate contradiction query.

### Reference influence

- Our own design.
- Open Collider for adjacent-domain terms.

---

## Phase 7: Literature Retrieval and Ranking

### Goal

Retrieve high-quality paper sets.

### Required retrieval groups

1. Top 20 high-impact papers from last 5 years.
2. Top 20 recent frontier papers from last 6–12 months.
3. 5–10 review/survey papers.
4. Related prior-art papers.
5. Contradictory papers.
6. Dataset/benchmark papers.

### Reference influence

- User’s latest logic.
- Agent Laboratory.
- ScienceClaw.

---

## Phase 8: Paper Analysis

### Goal

Extract structured claims from papers.

### Steps

1. Analyze abstract.
2. Retrieve legal full text if available.
3. Extract problem.
4. Extract method.
5. Extract data/sample.
6. Extract metrics.
7. Extract findings.
8. Extract limitations.
9. Extract future work.
10. Link extracted facts to sources.

### Reference influence

- ScienceClaw for citation discipline.
- PaperOrchestra for literature review fields.

---

## Phase 9: Clustering and Literature Map

### Goal

Group papers into themes.

### Steps

1. Embed papers.
2. Cluster by semantic similarity.
3. Cluster by method.
4. Cluster by dataset.
5. Cluster by metric.
6. Label clusters.
7. Select representative papers.
8. Generate cluster summaries.
9. Store cluster records.
10. Prepare visualization.

### Reference influence

- WeKnora for knowledge organization.
- Our conflict-driven research design.

---

## Phase 10: Conflict and Gap Detection

### Goal

Identify research opportunities.

### Steps

1. Compare findings inside clusters.
2. Compare methods.
3. Compare datasets.
4. Compare metrics.
5. Compare assumptions.
6. Find repeated limitations.
7. Find missing baselines.
8. Find weak validation.
9. Find frontier-vs-landmark tensions.
10. Store opportunities.

### Reference influence

This is one of our core original components.

---

## Phase 11: Research Question Generation

### Goal

Turn conflicts into research questions.

### Steps

1. Generate questions from conflicts.
2. Generate questions from limitations.
3. Generate questions from frontier changes.
4. Generate cross-domain questions.
5. Deduplicate questions.
6. Score questions.
7. Select top questions.
8. Store rejected questions.
9. Link questions to evidence.
10. Prepare hypotheses.

### Reference influence

- Open Collider for creative cross-domain question generation.
- ScienceClaw for evidence discipline.

---

## Phase 12: Hypothesis Generation

### Goal

Create testable hypotheses.

### Steps

1. Select top research questions.
2. Define variables.
3. Define expected relationship.
4. Define context.
5. Define baseline.
6. Define metric.
7. Define dataset.
8. Define failure condition.
9. Generate hypothesis record.
10. Store version history.

### Reference influence

- freephdlabor.
- Agent Laboratory.
- AI-Scientist.

---

## Phase 13: Validation Planning

### Goal

Design test paths.

### Steps

1. Search datasets.
2. Search benchmarks.
3. Identify baselines.
4. Define experiment.
5. Define metrics.
6. Define statistical tests.
7. Define simulation path if needed.
8. Estimate cost.
9. Estimate feasibility.
10. Update idea score.

### Reference influence

- freephdlabor ExperimentationAgent.
- PhysicsIntern verification mindset.
- MathCode for formal validation when applicable.

---

## Phase 14: Idea Scoring and Ledger

### Goal

Score, classify, and preserve all ideas.

### Steps

1. Score novelty.
2. Score feasibility.
3. Score importance.
4. Score evidence support.
5. Score validation clarity.
6. Score differentiation.
7. Score prior-art risk.
8. Classify idea.
9. Explain classification.
10. Store in ledger.

### Classification

```text
High-value
Promising
Incremental
Weak
Reject
```

### Reference influence

This is mostly our original product differentiator.

---

## Phase 15: Idle Cognition Engine

### Goal

Allow the system to conduct background research.

### Steps

1. Implement idle detector.
2. Implement scheduler.
3. Implement budget manager.
4. Implement idle mode selector.
5. Implement citation-conflict cycle.
6. Implement frontier scan cycle.
7. Implement rejected-idea revival cycle.
8. Implement cross-domain collision cycle.
9. Implement skill-improvement cycle.
10. Generate idle reports.

### Reference influence

- freephdlabor for 24/7 research ambition.
- Open Collider for non-trivial idea generation.
- ScienceClaw for memory-driven continuity.

---

## Phase 16: Skill Memory

### Goal

Make the system learn how to research.

### Steps

1. Implement skill schema.
2. Implement skill creation.
3. Implement skill retrieval.
4. Implement skill usage logs.
5. Implement skill scoring.
6. Implement skill versioning.
7. Implement skill lifecycle.
8. Implement skill retirement.
9. Implement skill browser.
10. Add skill tests.

### Reference influence

- SkillX for skill hierarchy.
- ScienceClaw for self-evolving skills.
- academic-research-skills for academic skill patterns.
- PaperOrchestra for skill-file conventions.

---

## Phase 17: Data Analysis Sandbox

### Goal

Run safe analysis.

### Steps

1. Build Docker sandbox.
2. Restrict filesystem.
3. Restrict network by policy.
4. Add dataset upload.
5. Add dataset metadata.
6. Generate analysis scripts.
7. Execute scripts.
8. Capture outputs.
9. Store artifacts.
10. Link results to hypotheses.

### Reference influence

- DeerFlow sandboxing.
- freephdlabor experiment tools.
- PhysicsIntern reproducibility.

---

## Phase 18: Multi-Agent Runtime

### Goal

Formalize specialized agents.

### Agents

1. Orchestrator Agent.
2. User Intent Agent.
3. Idle Cognition Agent.
4. Literature Agent.
5. Paper Analyst Agent.
6. Cluster Agent.
7. Conflict Agent.
8. Research Question Agent.
9. Hypothesis Agent.
10. Validation Planner Agent.
11. Data Analyst Agent.
12. Skeptic Agent.
13. Decision Agent.
14. Skill Curator Agent.
15. Archivist Agent.

### Reference influence

- DeerFlow for subagents.
- freephdlabor for manager/specialist pattern.
- PhysicsIntern for reviewer/critic pattern.

---

## Phase 19: Knowledge Base and Research Wiki

### Goal

Create persistent readable memory.

### Steps

1. Generate paper notes.
2. Generate cluster notes.
3. Generate conflict notes.
4. Generate hypothesis notes.
5. Generate skill notes.
6. Generate project summaries.
7. Link notes.
8. Add semantic search.
9. Add export.
10. Add update cycle.

### Reference influence

- WeKnora.
- Claude Scholar.
- ScienceClaw.

---

## Phase 20: Dashboard

### Goal

Make the system usable.

### Views

1. Project overview.
2. Active run.
3. Idle cycles.
4. Idea ledger.
5. Idea detail.
6. Paper table.
7. Cluster/conflict map.
8. Research questions.
9. Hypotheses.
10. Validation plans.
11. Skills.
12. Reports.
13. Research wiki.
14. Approval queue.
15. Settings.

### Reference influence

- Claude Scholar.
- Claude Prism.
- PaperDebugger.

---

## Phase 21: Reporting and Manuscript Support

### Goal

Generate professional research outputs.

### Steps

1. Generate Markdown reports.
2. Generate HTML reports.
3. Generate PDF reports.
4. Generate CSV tables.
5. Generate JSON exports.
6. Generate LaTeX outline.
7. Generate related-work draft.
8. Generate method draft.
9. Run review agent.
10. Run layout repair later.

### Reference influence

- PaperOrchestra.
- PaperDebugger.
- PaperFit.
- stop-slop.

---

## Phase 22: Evaluation and Benchmarking

### Goal

Prove the system works.

### Baselines

1. One-shot LLM idea generation.
2. Static literature review agent.
3. AI-Scientist-style automated discovery baseline where applicable.
4. Agent Laboratory-style assisted research baseline.
5. Human researcher baseline later, if available.

### Metrics

- Novelty score.
- Feasibility score.
- Prior-art overlap.
- Validation-plan quality.
- Expert rating.
- Skill reuse benefit.
- Idle idea value.
- Rejection accuracy.

### Reference influence

- AI-Scientist as prior-art benchmark.
- PaperOrchestra autorater idea.

---

## Phase 23: Security, Permissions, and Compliance

### Goal

Make autonomy safe.

### Rules

Always allowed:

- Search allowed academic APIs.
- Generate ideas.
- Analyze allowed papers.
- Write reports.
- Create skills.
- Run sandboxed analysis.

Approval required:

- Emailing people.
- Publishing content.
- Submitting papers.
- Spending money.
- Accessing private accounts.
- Downloading restricted datasets.
- Changing safety settings.

Never allowed by default:

- Bypassing paywalls.
- Scraping disallowed sources.
- Fabricating citations.
- Hiding failed searches.
- Deleting rejection history.
- Disabling audit logs.
- Treating simulated data as real.

---

## Phase 24: Packaging and Deployment

### Goal

Make the system installable.

### Steps

1. Docker Compose.
2. Local install script.
3. Environment template.
4. Setup wizard.
5. API key configuration.
6. Database initialization.
7. Example project.
8. Sample research run.
9. Troubleshooting guide.
10. Release notes.

---

## Phase 25: Full-System Release

### Release acceptance criteria

The system is complete when it can:

1. Accept a strict user idea and research it without pivoting.
2. Accept a flexible idea and adapt it when justified.
3. Start idle research when enabled.
4. Retrieve academic literature.
5. Find high-impact and frontier papers.
6. Cluster papers.
7. Detect conflicts.
8. Generate research questions.
9. Form hypotheses.
10. Design validation plans.
11. Analyze data in a sandbox.
12. Score and classify ideas.
13. Store all ideas and rejection reasons.
14. Create skills.
15. Reuse skills.
16. Generate reports.
17. Maintain a research wiki.
18. Show everything in a dashboard.
19. Enforce safety and approvals.
20. Preserve complete audit logs.

---

## 7. Recommended Technical Stack

### Backend

```text
Python
FastAPI
PostgreSQL
SQLAlchemy or SQLModel
Alembic
Redis
Celery / RQ / Dramatiq / APScheduler
Docker
Pydantic
```

### Vector Search

```text
pgvector or Qdrant
```

### Frontend

```text
Next.js or React
Tailwind CSS
Markdown renderer
Charting library
Table/grid library
```

### Agent Runtime

```text
LangGraph-style durable workflow engine
OpenAI Agents SDK-style agent/tool/handoff layer
Optional DeerFlow-inspired message gateway
```

### Academic APIs

```text
OpenAlex
Semantic Scholar
Crossref
arXiv
PubMed / Europe PMC
DOAJ / CORE / Unpaywall
```

### Data Analysis

```text
Docker sandbox
Python
Pandas
NumPy
SciPy
scikit-learn
statsmodels
matplotlib
Jupyter-compatible artifacts
```

### Knowledge Base

```text
PostgreSQL
Vector database
Markdown notes
Knowledge graph later
```

---

## 8. Core Database Tables

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

## 9. How the Reference Projects Combine into Our Final System

The final system should be assembled like this:

```text
ScienceClaw
→ Scientific memory, self-evolving skills, citation discipline

DeerFlow
→ Long-horizon orchestration, subagents, tools, sandboxes

freephdlabor
→ Scientific lifecycle agents and 24/7 research ambition

Agent Laboratory
→ Literature → experiment → report workflow

AI-Scientist
→ Automated discovery benchmark and prior-art awareness

SkillX
→ Skill hierarchy and skill knowledge-base construction

Open Collider
→ Cross-domain idle ideation

WeKnora
→ RAG, self-maintaining wiki, knowledge base

PhysicsIntern
→ Structured state, critique, reproducibility

Claude Scholar
→ Research workspace and human review workflow

academic-research-skills
→ Academic skill-pack conventions

PaperOrchestra
→ Paper writing, plotting, literature review, refinement

Claude Prism
→ Offline scientific writing workspace

PaperDebugger
→ Academic editing/review stage

PaperFit
→ LaTeX layout repair stage

MathCode
→ Formal math validation stage

CodeGraph
→ Codebase understanding stage

stop-slop
→ Minor prose cleanup only

humanize-text
→ Do not use

Awesome-Deep-Research
→ Landscape monitoring
```

---

## 10. The Most Important Differentiator

The project should not compete by saying:

```text
We automate scientific research.
```

That is too broad and already claimed by other systems.

The stronger differentiator is:

```text
We build a persistent scientific cognition system that keeps an idea ledger, detects literature conflicts, generates hypotheses during idle time, rejects weak ideas with reasons, and learns reusable research skills from every cycle.
```

That is more specific, more defensible, and more valuable.

---

## 11. First Complete Use Case

The first full-system demonstration should be:

```text
Subject: Autonomous research agents
Idle mode: Citation-conflict question generation
```

Expected workflow:

1. The project is active.
2. User is idle.
3. System starts an idle cycle.
4. It resolves the subject.
5. It retrieves 20 highly cited papers from the past 5 years.
6. It retrieves 20 frontier papers from the past 12 months.
7. It retrieves review papers.
8. It builds a paper table.
9. It clusters the papers into 5–8 themes.
10. It finds conflicts inside clusters.
11. It generates at least 10 research questions.
12. It converts top questions into hypotheses.
13. It designs validation plans.
14. It scores ideas.
15. It classifies ideas.
16. It stores rejected ideas with reasons.
17. It creates or updates at least one research skill.
18. It generates a report.
19. It updates the research wiki.
20. It shows results in the dashboard.

---

## 12. Non-Negotiable Product Rules

1. Every idea must be stored.
2. Every rejected idea must include a rejection reason.
3. Every score must be explainable.
4. Every research run must have an audit trail.
5. Every paper-derived claim must link to a source.
6. The system must not claim guaranteed novelty.
7. Idle autonomy must respect budget and scope.
8. Skills must be evaluated and versioned.
9. The system must not bypass access restrictions.
10. The system must not hide failed searches.
11. The system must not disable logging.
12. The system must not publish or communicate externally without approval.
13. The system must distinguish real data from simulated data.
14. Humanize/detector-bypass tools must not be used.
15. Scientific rigor is more important than producing impressive text.

---

## 13. Final Recommendation

Build a new original system.

Do not fork one project as the whole base.

Use this reference pattern:

```text
Conceptual center: ScienceClaw
Engineering runtime: DeerFlow-style long-horizon orchestration
Scientific lifecycle: freephdlabor + Agent Laboratory
Automated-discovery prior art: AI-Scientist
Skill learning: SkillX
Idle creativity: Open Collider
Knowledge base: WeKnora
Research state: PhysicsIntern
Paper output: PaperOrchestra + PaperDebugger + PaperFit
```

The complete product should be built around our own core loop:

```text
User Prompt or Idle Trigger
→ Autonomy/Flexibility Decision
→ Literature Retrieval
→ Paper Clustering
→ Conflict Detection
→ Research Question Generation
→ Hypothesis Generation
→ Validation Planning
→ Data Analysis if available
→ Idea Scoring
→ Idea Ledger
→ Skill Creation
→ Skill Reuse
→ Report and Wiki Update
```

This combined architecture is stronger than any single reference project because it adds the missing layer: persistent, evidence-based, self-improving research cognition.

