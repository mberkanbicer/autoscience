# API Design

## Overview

REST API built with FastAPI. All endpoints return JSON. UUIDs for all identifiers. Consistent error format. Pagination for list endpoints.

---

## Base URL

```
http://localhost:8000/api/v1
```

## Common Response Format

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100
  }
}
```

## Error Format

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [...]
  }
}
```

---

## Endpoints

### Projects

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects` | List all projects |
| POST | `/projects` | Create a project |
| GET | `/projects/{id}` | Get project details |
| PUT | `/projects/{id}` | Update project |
| DELETE | `/projects/{id}` | Delete project |
| GET | `/projects/{id}/settings` | Get project settings |
| PUT | `/projects/{id}/settings` | Update project settings |
| GET | `/projects/{id}/stats` | Get project statistics |

### Ideas

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects/{id}/ideas` | List ideas for project |
| POST | `/projects/{id}/ideas` | Create an idea |
| GET | `/ideas/{id}` | Get idea details |
| PUT | `/ideas/{id}` | Update idea |
| GET | `/ideas/{id}/versions` | Get idea version history |
| GET | `/ideas/{id}/scores` | Get idea score history |
| GET | `/ideas/{id}/decisions` | Get idea decision history |
| GET | `/ideas/{id}/linked` | Get linked papers, conflicts, questions |
| POST | `/ideas/{id}/revive` | Revive a rejected idea |

### Research Runs

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects/{id}/runs` | List runs for project |
| POST | `/projects/{id}/runs` | Start a new research run |
| GET | `/runs/{id}` | Get run details |
| POST | `/runs/{id}/pause` | Pause a run |
| POST | `/runs/{id}/resume` | Resume a run |
| POST | `/runs/{id}/cancel` | Cancel a run |
| GET | `/runs/{id}/events` | Get run event timeline |
| GET | `/runs/{id}/state` | Get current run state |
| GET | `/runs/{id}/tools` | Get tool calls for run |

### Papers

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects/{id}/papers` | List papers for project |
| POST | `/projects/{id}/papers/search` | Search and add papers |
| GET | `/papers/{id}` | Get paper details |
| GET | `/papers/{id}/analysis` | Get paper analysis |
| GET | `/papers/{id}/clusters` | Get clusters containing paper |
| POST | `/papers/{id}/analyze` | Trigger paper analysis |

### Clusters

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects/{id}/clusters` | List clusters for project |
| GET | `/clusters/{id}` | Get cluster details |
| GET | `/clusters/{id}/papers` | Get papers in cluster |
| GET | `/clusters/{id}/conflicts` | Get conflicts in cluster |

### Conflicts

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects/{id}/conflicts` | List conflicts for project |
| GET | `/conflicts/{id}` | Get conflict details |
| GET | `/conflicts/{id}/papers` | Get supporting/opposing papers |

### Research Questions

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects/{id}/questions` | List questions for project |
| POST | `/projects/{id}/questions/generate` | Generate questions from conflicts |
| GET | `/questions/{id}` | Get question details |
| GET | `/questions/{id}/hypothesis` | Get linked hypothesis |

### Hypotheses

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects/{id}/hypotheses` | List hypotheses for project |
| POST | `/projects/{id}/hypotheses` | Create hypothesis from question |
| GET | `/hypotheses/{id}` | Get hypothesis details |
| PUT | `/hypotheses/{id}` | Update hypothesis |
| GET | `/hypotheses/{id}/validation` | Get validation plan |

### Validation Plans

| Method | Endpoint | Description |
|---|---|---|
| GET | `/hypotheses/{id}/validation` | Get validation plan |
| POST | `/hypotheses/{id}/validation` | Create validation plan |
| PUT | `/validation/{id}` | Update validation plan |

### Skills

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects/{id}/skills` | List skills for project |
| GET | `/skills/{id}` | Get skill details |
| PUT | `/skills/{id}` | Update skill |
| GET | `/skills/{id}/versions` | Get skill version history |
| GET | `/skills/{id}/usage` | Get skill usage history |
| POST | `/skills/{id}/retire` | Retire a skill |

### Reports

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects/{id}/reports` | List reports for project |
| GET | `/reports/{id}` | Get report details |
| GET | `/reports/{id}/markdown` | Get report as Markdown |
| GET | `/reports/{id}/html` | Get report as HTML |
| POST | `/projects/{id}/reports/generate` | Generate report for project |

### Knowledge Wiki

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects/{id}/wiki` | Get wiki overview |
| GET | `/projects/{id}/wiki/{section}` | Get wiki section |
| GET | `/projects/{id}/wiki/search` | Search wiki |
| POST | `/projects/{id}/wiki/regenerate` | Regenerate wiki |

### Idle Cognition

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects/{id}/idle/cycles` | List idle cycles |
| GET | `/projects/{id}/idle/status` | Get idle engine status |
| POST | `/projects/{id}/idle/start` | Manually start idle cycle |
| POST | `/projects/{id}/idle/stop` | Stop idle engine |

### Datasets

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects/{id}/datasets` | List datasets |
| POST | `/projects/{id}/datasets/upload` | Upload dataset |
| GET | `/datasets/{id}` | Get dataset details |
| GET | `/datasets/{id}/analyses` | Get analysis runs for dataset |

### Approvals

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects/{id}/approvals` | List pending approvals |
| POST | `/approvals/{id}/approve` | Approve action |
| POST | `/approvals/{id}/deny` | Deny action |

### Audit

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects/{id}/audit` | List audit logs |
| GET | `/runs/{id}/audit` | List audit logs for run |
| GET | `/audit/{id}` | Get audit log detail |

### Search

| Method | Endpoint | Description |
|---|---|---|
| GET | `/projects/{id}/search` | Search across all project data |

---

## Request/Response Examples

### Create Project

```json
POST /api/v1/projects
{
  "name": "Autonomous Scientific Research Brain",
  "domain": "AI research automation",
  "description": "Building a self-learning research system",
  "subject_scope": [
    "autonomous research agents",
    "scientific discovery automation",
    "literature-based discovery",
    "hypothesis generation"
  ],
  "out_of_scope": [
    "unrelated consumer apps",
    "military applications"
  ],
  "default_flexibility": 0.6,
  "idle_research_enabled": true,
  "idle_trigger_minutes": 120,
  "max_idle_cycles_per_day": 3,
  "max_sources_per_cycle": 50
}

Response:
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Autonomous Scientific Research Brain",
    "domain": "AI research automation",
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

### Create Idea

```json
POST /api/v1/projects/{id}/ideas
{
  "text": "An agent that researches during idle time by detecting conflicts in scientific literature",
  "flexibility": 0.75
}

Response:
{
  "success": true,
  "data": {
    "id": "...",
    "origin": "user_prompt",
    "initial_text": "An agent that researches during idle time...",
    "current_text": "An agent that researches during idle time...",
    "flexibility": 0.75,
    "status": "active",
    "created_at": "..."
  }
}
```

### Start Research Run

```json
POST /api/v1/projects/{id}/runs
{
  "idea_id": "...",
  "run_type": "user_directed",
  "max_minutes": 60,
  "max_sources": 50,
  "max_cost_usd": 5.0
}

Response:
{
  "success": true,
  "data": {
    "id": "...",
    "state": "created",
    "run_type": "user_directed",
    "started_at": "..."
  }
}
```

### Get Idea with Scores

```json
GET /api/v1/ideas/{id}

Response:
{
  "success": true,
  "data": {
    "id": "...",
    "current_text": "...",
    "status": "active",
    "classification": "promising",
    "overall_score": 7.2,
    "scores": {
      "novelty": 8.0,
      "feasibility": 7.5,
      "importance": 7.0,
      "evidence_support": 6.5,
      "validation_clarity": 7.8,
      "differentiation": 7.5,
      "data_availability": 6.0,
      "skill_leverage": 5.0,
      "user_alignment": 8.0,
      "prior_art_risk": 3.0,
      "safety_risk": 1.0,
      "cost_risk": 2.0
    },
    "classification_reason": "The idea combines idle research with conflict detection in a novel way...",
    "linked_papers": [...],
    "linked_conflicts": [...],
    "linked_questions": [...],
    "linked_hypotheses": [...]
  }
}
```

### Search Papers

```json
POST /api/v1/projects/{id}/papers/search
{
  "query": "autonomous research agents",
  "sources": ["openalex", "semantic_scholar", "arxiv"],
  "year_range": [2020, 2025],
  "limit": 50
}

Response:
{
  "success": true,
  "data": {
    "search_id": "...",
    "total_results": 234,
    "papers_added": 50,
    "papers": [...]
  }
}
```

---

## Authentication

Initially, no authentication (single-user local deployment). Future versions will support:

- API key authentication
- JWT tokens
- OAuth2

---

## Rate Limiting

Per-connector rate limits enforced:

| Connector | Rate Limit |
|---|---|
| OpenAlex | 10 requests/second |
| Semantic Scholar | 100 requests/5 minutes (with key) |
| Crossref | 50 requests/second |
| arXiv | 3 requests/3 seconds |
| PubMed | 3 requests/second |

---

## Pagination

All list endpoints support pagination:

```
GET /api/v1/projects?page=1&per_page=20
```

Response includes `meta` with page, per_page, total.

---

## Filtering and Sorting

List endpoints support filtering and sorting:

```
GET /api/v1/projects/{id}/ideas?status=active&classification=promising&sort=overall_score&order=desc
```

---

## WebSocket Endpoints (Future)

For real-time updates during research runs:

```
WS /api/v1/runs/{id}/events
```

Sends `ResearchRunEvent` objects as they occur.
