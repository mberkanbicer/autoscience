# Data Model

## Overview

The system is database-first. All state lives in PostgreSQL. Every entity has UUID primary keys, created_at/updated_at timestamps, and soft-delete support where appropriate.

---

## Entity Relationship Diagram (Text)

```
Users ──< Projects ──< Ideas ──< IdeaVersions
                   │            ──< IdeaScores
                   │            ──< IdeaClassifications
                   │            ──< IdeaDecisions
                   │
                   ├──< ResearchRuns ──< ResearchRunEvents
                   │              ──< ToolCalls
                   │
                   ├──< IdleCycles
                   │
                   ├──< Papers ──< PaperSources
                   │         ──< PaperFulltexts
                   │         ──< PaperEmbeddings
                   │         ──< PaperAnalyses
                   │
                   ├──< PaperClusters ──< ClusterLabels
                   │              ──< ClusterConflicts
                   │
                   ├──< ResearchQuestions
                   │
                   ├──< Hypotheses ──< ValidationPlans
                   │
                   ├──< Datasets ──< AnalysisRuns ──< AnalysisArtifacts
                   │
                   ├──< Skills ──< SkillVersions
                   │         ──< SkillUsages
                   │         ──< SkillEvaluations
                   │
                   ├──< ResearchReports
                   │
                   ├──< KnowledgeNotes
                   │
                   └──< AuditLogs
                       ApprovalRequests
                       SystemEvents
```

---

## Tables

### Users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    display_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'researcher',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

### Projects

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(500) NOT NULL,
    description TEXT,
    subject_scope JSONB DEFAULT '[]',
    out_of_scope JSONB DEFAULT '[]',
    default_flexibility FLOAT DEFAULT 0.6,
    idle_research_enabled BOOLEAN DEFAULT true,
    idle_trigger_minutes INTEGER DEFAULT 120,
    max_idle_cycles_per_day INTEGER DEFAULT 3,
    max_sources_per_cycle INTEGER DEFAULT 50,
    approval_required_for_external_actions BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

### Ideas

```sql
CREATE TABLE ideas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    origin VARCHAR(50) NOT NULL,  -- user_prompt | idle_generated | literature_gap | skill_generated | revived
    initial_text TEXT NOT NULL,
    current_text TEXT NOT NULL,
    flexibility FLOAT,
    status VARCHAR(50) DEFAULT 'active',  -- active | archived | rejected | promoted | under_validation
    classification VARCHAR(50),
    overall_score FLOAT,
    classification_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE TABLE idea_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idea_id UUID REFERENCES ideas(id) NOT NULL,
    version_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    change_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE idea_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idea_id UUID REFERENCES ideas(id) NOT NULL,
    novelty FLOAT,
    feasibility FLOAT,
    importance FLOAT,
    evidence_support FLOAT,
    validation_clarity FLOAT,
    differentiation FLOAT,
    data_availability FLOAT,
    skill_leverage FLOAT,
    user_alignment FLOAT,
    prior_art_risk FLOAT,
    safety_risk FLOAT,
    cost_risk FLOAT,
    overall_value FLOAT,
    scoring_rationale TEXT,
    scored_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE idea_classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idea_id UUID REFERENCES ideas(id) NOT NULL,
    classification VARCHAR(50) NOT NULL,
    score FLOAT,
    reason TEXT,
    classified_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE idea_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idea_id UUID REFERENCES ideas(id) NOT NULL,
    run_id UUID REFERENCES research_runs(id),
    decision VARCHAR(50) NOT NULL,  -- continue | revise | pivot | archive | reject | promote
    reason TEXT,
    decided_at TIMESTAMP DEFAULT NOW()
);
```

### Research Runs

```sql
CREATE TABLE research_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    idea_id UUID REFERENCES ideas(id),
    run_type VARCHAR(50) NOT NULL,  -- user_directed | flexible_user | idle_autonomous | validation | skill_refinement
    state VARCHAR(50) DEFAULT 'created',  -- created | running | paused | waiting_for_approval | completed | failed | cancelled
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    max_minutes INTEGER DEFAULT 60,
    max_sources INTEGER DEFAULT 50,
    max_cost_usd FLOAT DEFAULT 5.0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE research_run_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES research_runs(id) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    actor VARCHAR(100),
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Papers

```sql
CREATE TABLE papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    title TEXT NOT NULL,
    authors JSONB DEFAULT '[]',
    year INTEGER,
    doi VARCHAR(255),
    abstract TEXT,
    venue VARCHAR(500),
    url TEXT,
    citation_count INTEGER,
    paper_type VARCHAR(50),  -- research | review | survey | dataset | benchmark
    source_connector VARCHAR(100),
    source_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE TABLE paper_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID REFERENCES papers(id) NOT NULL,
    connector VARCHAR(100) NOT NULL,
    external_id VARCHAR(255),
    raw_metadata JSONB,
    fetched_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE paper_fulltexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID REFERENCES papers(id) NOT NULL,
    fulltext TEXT,
    language VARCHAR(10),
    fetched_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE paper_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID REFERENCES papers(id) NOT NULL,
    embedding VECTOR(1536),
    model_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE paper_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID REFERENCES papers(id) NOT NULL,
    problem TEXT,
    method TEXT,
    dataset_sample TEXT,
    metrics JSONB DEFAULT '[]',
    findings JSONB DEFAULT '[]',
    limitations JSONB DEFAULT '[]',
    future_work JSONB DEFAULT '[]',
    assumptions JSONB DEFAULT '[]',
    relation_to_idea TEXT,
    key_claims JSONB DEFAULT '[]',
    confidence FLOAT,
    analyzed_at TIMESTAMP DEFAULT NOW()
);
```

### Clusters

```sql
CREATE TABLE paper_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    name VARCHAR(255),
    description TEXT,
    cluster_type VARCHAR(50),  -- topic | method | dataset | claim | application
    paper_ids JSONB DEFAULT '[]',
    representative_paper_id UUID REFERENCES papers(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE cluster_labels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id UUID REFERENCES paper_clusters(id) NOT NULL,
    label VARCHAR(255) NOT NULL,
    rationale TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Conflicts

```sql
CREATE TABLE cluster_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    cluster_id UUID REFERENCES paper_clusters(id),
    conflict_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    supporting_papers JSONB DEFAULT '[]',
    opposing_papers JSONB DEFAULT '[]',
    research_opportunity TEXT,
    severity FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Research Questions

```sql
CREATE TABLE research_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    idea_id UUID REFERENCES ideas(id),
    run_id UUID REFERENCES research_runs(id),
    question TEXT NOT NULL,
    source_conflicts JSONB DEFAULT '[]',
    source_gaps JSONB DEFAULT '[]',
    rank FLOAT,
    status VARCHAR(50) DEFAULT 'generated',  -- generated | selected | hypothesis_created | rejected
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Hypotheses

```sql
CREATE TABLE hypotheses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    idea_id UUID REFERENCES ideas(id),
    question_id UUID REFERENCES research_questions(id),
    statement TEXT NOT NULL,
    independent_variable TEXT,
    dependent_variable TEXT,
    context TEXT,
    expected_direction TEXT,
    baseline TEXT,
    metric TEXT,
    dataset_requirement TEXT,
    failure_condition TEXT,
    confidence FLOAT,
    version INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'draft',  -- draft | validated | rejected | promoted
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

### Validation Plans

```sql
CREATE TABLE validation_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hypothesis_id UUID REFERENCES hypotheses(id) NOT NULL,
    dataset_candidates JSONB DEFAULT '[]',
    benchmark_candidates JSONB DEFAULT '[]',
    baselines JSONB DEFAULT '[]',
    metrics JSONB DEFAULT '[]',
    experimental_design TEXT,
    statistical_tests JSONB DEFAULT '[]',
    simulation_option TEXT,
    expected_artifacts JSONB DEFAULT '[]',
    difficulty_estimate FLOAT,
    cost_estimate FLOAT,
    feasibility_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Datasets and Analysis

```sql
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    name VARCHAR(255),
    description TEXT,
    source_url TEXT,
    format VARCHAR(50),
    size_bytes BIGINT,
    row_count INTEGER,
    column_count INTEGER,
    schema_json JSONB,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE analysis_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hypothesis_id UUID REFERENCES hypotheses(id),
    dataset_id UUID REFERENCES datasets(id),
    script TEXT,
    status VARCHAR(50),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

CREATE TABLE analysis_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID REFERENCES analysis_runs(id) NOT NULL,
    artifact_type VARCHAR(50),  -- figure | table | json | csv | script
    file_path TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Skills

```sql
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    name VARCHAR(255) NOT NULL,
    skill_type VARCHAR(50) NOT NULL,
    purpose TEXT,
    trigger_conditions JSONB DEFAULT '[]',
    inputs JSONB DEFAULT '[]',
    procedure JSONB DEFAULT '[]',
    outputs JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'candidate',
    version VARCHAR(20) DEFAULT '1.0',
    times_used INTEGER DEFAULT 0,
    successful_uses INTEGER DEFAULT 0,
    average_score_improvement FLOAT,
    failure_cases JSONB DEFAULT '[]',
    domains_where_it_works JSONB DEFAULT '[]',
    domains_where_it_fails JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE TABLE skill_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id UUID REFERENCES skills(id) NOT NULL,
    version VARCHAR(20) NOT NULL,
    changes TEXT,
    procedure JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE skill_usages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id UUID REFERENCES skills(id) NOT NULL,
    run_id UUID REFERENCES research_runs(id),
    success BOOLEAN,
    score_before FLOAT,
    score_after FLOAT,
    notes TEXT,
    used_at TIMESTAMP DEFAULT NOW()
);
```

### Reports

```sql
CREATE TABLE research_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    run_id UUID REFERENCES research_runs(id),
    idea_id UUID REFERENCES ideas(id),
    title VARCHAR(500),
    content_markdown TEXT,
    content_html TEXT,
    report_type VARCHAR(50),  -- cycle | idle | validation | summary
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Knowledge Notes

```sql
CREATE TABLE knowledge_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    note_type VARCHAR(50) NOT NULL,  -- paper | cluster | conflict | hypothesis | skill | project
    entity_id UUID,
    title VARCHAR(255),
    content TEXT,
    embedding VECTOR(1536),
    linked_notes JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

### Audit and Approvals

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    run_id UUID REFERENCES research_runs(id),
    event_type VARCHAR(100) NOT NULL,
    actor VARCHAR(100),
    action TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tool_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES research_runs(id),
    agent_role VARCHAR(100),
    tool_name VARCHAR(255),
    input_json JSONB,
    output_json JSONB,
    duration_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    run_id UUID REFERENCES research_runs(id),
    action_type VARCHAR(100),
    action_description TEXT,
    action_payload JSONB,
    status VARCHAR(50) DEFAULT 'pending',  -- pending | approved | denied
    reviewer_notes TEXT,
    requested_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

CREATE TABLE system_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100),
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Idle Cycles

```sql
CREATE TABLE idle_cycles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    run_id UUID REFERENCES research_runs(id),
    idle_mode VARCHAR(50),  -- frontier_scan | citation_conflict | revisit_rejected | cross_domain | skill_improvement | dataset_discovery
    trigger_reason TEXT,
    ideas_generated INTEGER DEFAULT 0,
    questions_generated INTEGER DEFAULT 0,
    hypotheses_generated INTEGER DEFAULT 0,
    skills_created INTEGER DEFAULT 0,
    duration_seconds INTEGER,
    cost_usd FLOAT,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

### Literature Search Tracking

```sql
CREATE TABLE literature_searches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    run_id UUID REFERENCES research_runs(id),
    idea_id UUID REFERENCES ideas(id),
    total_results INTEGER,
    papers_selected INTEGER,
    queries_used JSONB DEFAULT '[]',
    connectors_used JSONB DEFAULT '[]',
    searched_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE search_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    search_id UUID REFERENCES literature_searches(id) NOT NULL,
    query_text TEXT NOT NULL,
    query_type VARCHAR(50),
    sources JSONB DEFAULT '[]',
    year_range JSONB,
    result_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Indexes

```sql
-- Performance-critical indexes
CREATE INDEX idx_ideas_project ON ideas(project_id);
CREATE INDEX idx_ideas_status ON ideas(status);
CREATE INDEX idx_ideas_classification ON ideas(classification);
CREATE INDEX idx_papers_project ON papers(project_id);
CREATE INDEX idx_papers_doi ON papers(doi);
CREATE INDEX idx_papers_year ON papers(year);
CREATE INDEX idx_research_runs_project ON research_runs(project_id);
CREATE INDEX idx_research_runs_state ON research_runs(state);
CREATE INDEX idx_research_run_events_run ON research_run_events(run_id);
CREATE INDEX idx_paper_analyses_paper ON paper_analyses(paper_id);
CREATE INDEX idx_cluster_conflicts_project ON cluster_conflicts(project_id);
CREATE INDEX idx_research_questions_project ON research_questions(project_id);
CREATE INDEX idx_hypotheses_project ON hypotheses(project_id);
CREATE INDEX idx_skills_project ON skills(project_id);
CREATE INDEX idx_skills_status ON skills(status);
CREATE INDEX idx_audit_logs_project ON audit_logs(project_id);
CREATE INDEX idx_audit_logs_run ON audit_logs(run_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_knowledge_notes_project ON knowledge_notes(project_id);
CREATE INDEX idx_idle_cycles_project ON idle_cycles(project_id);

-- Vector indexes for semantic search
CREATE INDEX idx_paper_embeddings ON paper_embeddings USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_knowledge_notes_embedding ON knowledge_notes USING ivfflat (embedding vector_cosine_ops);
```

---

## Key Relationships

| Relationship | Type | Description |
|---|---|---|
| Project → Ideas | One-to-Many | A project has many ideas |
| Idea → IdeaVersions | One-to-Many | Ideas have version history |
| Idea → IdeaScores | One-to-Many | Ideas have score history |
| Project → ResearchRuns | One-to-Many | A project has many research runs |
| ResearchRun → ResearchRunEvents | One-to-Many | Runs have event timelines |
| Project → Papers | One-to-Many | A project has many papers |
| Paper → PaperAnalyses | One-to-One | Each paper has one analysis |
| Paper → PaperEmbeddings | One-to-One | Each paper has one embedding |
| Project → PaperClusters | One-to-Many | Papers grouped into clusters |
| Cluster → ClusterConflicts | One-to-Many | Clusters contain conflicts |
| Project → ResearchQuestions | One-to-Many | Questions derived from conflicts |
| Question → Hypothesis | One-to-One | Top questions become hypotheses |
| Hypothesis → ValidationPlan | One-to-One | Hypotheses have validation plans |
| Project → Skills | One-to-Many | Skills learned from research |
| Skill → SkillUsages | One-to-Many | Skills tracked by usage |
| ResearchRun → ToolCalls | One-to-Many | Runs log tool usage |
| Project → AuditLogs | One-to-Many | Complete audit trail |
