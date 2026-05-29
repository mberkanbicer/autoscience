# Development Standards

## Code Quality

### Python

- Python 3.11+
- Type hints on all function signatures
- Docstrings on all public functions and classes
- f-strings for string formatting
- async/await for I/O-bound operations
- No bare `except:` — always catch specific exceptions
- No `print()` in production code — use logging

### TypeScript/React

- TypeScript strict mode
- Functional components only (no class components)
- Props interfaces defined for all components
- No `any` type — use proper types
- Consistent naming: PascalCase for components, camelCase for functions/variables

### General

- YAGNI — don't build what you don't need
- KISS — keep it simple
- DRY — don't repeat yourself (but don't over-abstract)
- Explicit over implicit
- Small functions (< 50 lines ideally)
- Small files (< 500 lines ideally)

---

## Naming Conventions

### Python

| Element | Convention | Example |
|---|---|---|
| Files | snake_case | `paper_service.py` |
| Classes | PascalCase | `PaperService` |
| Functions | snake_case | `analyze_paper()` |
| Variables | snake_case | `paper_count` |
| Constants | UPPER_SNAKE_CASE | `MAX_PAPERS_PER_RUN` |
| Database tables | snake_case | `paper_analyses` |
| Database columns | snake_case | `created_at` |
| API endpoints | kebab-case | `/research-runs` |
| API parameters | snake_case | `query_type` |

### TypeScript

| Element | Convention | Example |
|---|---|---|
| Files | PascalCase (components) | `PaperTable.tsx` |
| Files | camelCase (utilities) | `api.ts` |
| Components | PascalCase | `PaperTable` |
| Functions | camelCase | `fetchPapers()` |
| Variables | camelCase | `paperCount` |
| Constants | UPPER_SNAKE_CASE | `MAX_PAPERS` |
| Types/Interfaces | PascalCase | `PaperAnalysis` |
| Props | PascalCase + Props suffix | `PaperTableProps` |

---

## File Organization

### Backend

```
backend/app/
├── models/          # SQLAlchemy models (database schema)
├── schemas/         # Pydantic schemas (API validation)
├── api/             # FastAPI route handlers
├── services/        # Business logic (no HTTP concerns)
├── agents/          # Agent definitions and logic
├── llm/             # LLM provider abstraction
├── connectors/      # External API connectors
├── engine/          # Core research engines
├── workflows/       # Durable workflow definitions
├── sandbox/         # Data analysis sandbox
└── utils/           # Shared utilities
```

**Rule:** No business logic in API routes. No database access in schemas. No HTTP concerns in services.

### Frontend

```
frontend/src/
├── app/             # Next.js pages and layouts
├── components/      # React components
│   ├── layout/      # Layout components (Header, Sidebar, Footer)
│   ├── projects/    # Project-related components
│   ├── ideas/       # Idea-related components
│   ├── papers/      # Paper-related components
│   ├── clusters/    # Cluster-related components
│   ├── skills/      # Skill-related components
│   ├── charts/      # Chart/visualization components
│   └── common/      # Shared components (Button, Modal, Table)
├── lib/             # Utilities (API client, types, helpers)
└── styles/          # Global styles
```

**Rule:** No API calls in components — use `lib/api.ts`. No inline styles — use Tailwind.

---

## Database Conventions

### Models

- All tables use UUID primary keys
- All tables have `created_at` (default: now) and `updated_at` (on update)
- Use `Mapped[]` type annotations with SQLAlchemy 2.0 style
- JSON columns for flexible arrays/objects
- Foreign keys explicitly defined
- Indexes on frequently queried columns
- No ORM relationships that cause N+1 queries without explicit loading

### Migrations

- Alembic for all schema changes
- Migration files are named: `YYYYMMDD_HHMMSS_description.py`
- Never edit existing migrations
- Always test migrations up and down
- Include data migrations when schema changes require data transformation

### Queries

- Use async SQLAlchemy sessions
- Eager load relationships when needed (selectinload, joinedload)
- Paginate all list queries
- Use database-level constraints (unique, check, not null)
- Avoid raw SQL unless performance-critical

---

## API Conventions

### REST

- Resources are plural nouns: `/projects`, `/ideas`, `/papers`
- Use HTTP methods: GET (read), POST (create), PUT (update), DELETE (delete)
- Nested resources for scoped access: `/projects/{id}/ideas`
- UUIDs in URLs, not slugs
- Consistent response format with `success`, `data`, `error`, `meta`
- Pagination with `page` and `per_page` query parameters
- Filtering with query parameters: `?status=active&classification=promising`
- Sorting with `sort` and `order`: `?sort=overall_score&order=desc`

### Validation

- Pydantic v2 for request/response validation
- Strict type checking
- Clear error messages
- Validate at API boundary, not in business logic

---

## LLM Prompt Conventions

- Prompts stored as Python functions in `llm/prompts/`
- Version-controlled (include version string)
- Token-efficient (no decorative language)
- Structured output format specified
- Temperature and model specified per use case
- Fallback prompt for provider-specific failures
- Log the prompt and response for audit

### Prompt Structure

```python
def analyze_paper_prompt(paper: Paper, idea: str, version: str = "1.0") -> list[Message]:
    return [
        SystemMessage(content=f"""You are a scientific paper analyst. Version: {version}.
Extract structured information from the paper.
Output JSON with the specified schema."""),
        UserMessage(content=f"""Paper: {paper.title}
Abstract: {paper.abstract}
Idea context: {idea}

Extract: problem, method, dataset, metrics, findings, limitations, future_work, assumptions.""")
    ]
```

---

## Testing Conventions

### Backend Tests

```
tests/
├── conftest.py          # Fixtures, test database setup
├── test_models/         # Model relationship tests
├── test_services/       # Business logic tests
├── test_connectors/     # Connector tests (mocked)
├── test_engines/        # Engine logic tests
├── test_agents/         # Agent behavior tests
└── test_api/            # API endpoint tests
```

- Unit tests for services and engines
- Integration tests for API endpoints
- Mock external APIs (LLM, academic sources)
- Test database with separate test database
- Run tests in isolation (no shared state)
- Aim for tests that verify behavior, not implementation

### Frontend Tests

- Component rendering tests
- User interaction tests
- API client tests
- No snapshot tests (brittle)

---

## Git Conventions

### Branches

- `main` — production-ready code
- `develop` — integration branch (future)
- `feature/description` — new features
- `fix/description` — bug fixes
- `docs/description` — documentation only

### Commits

- Conventional commits: `type(scope): description`
- Types: feat, fix, docs, style, refactor, test, chore
- Scope: component or area affected
- Description: imperative mood, < 72 characters
- Examples:
  - `feat(agents): implement paper analyst agent`
  - `fix(connectors): handle rate limit on OpenAlex`
  - `docs(api): add endpoint documentation`

### PRs

- One logical change per PR
- Clear description of what and why
- Tests pass
- No unrelated changes

---

## Logging

### Levels

- `DEBUG` — detailed diagnostic info
- `INFO` — normal operation events
- `WARNING` — unexpected but handled situations
- `ERROR` — failures that need attention
- `CRITICAL` — system-threatening failures

### What to Log

- Research run start/end/pause/resume
- Agent invocations
- Tool calls (input summary, output summary, duration)
- LLM calls (provider, model, token count, cost)
- External API calls (source, query, result count)
- Idea scoring and classification
- Skill creation and usage
- Errors and exceptions
- Approval requests and decisions

### What NOT to Log

- Full paper abstracts (too verbose)
- Full LLM responses (store in database instead)
- User API keys
- Passwords

---

## Error Handling

```python
# Backend
class ResearchError(Exception):
    """Base exception for research operations."""
    pass

class BudgetExceededError(ResearchError):
    """Raised when run budget is exhausted."""
    pass

class SourceUnavailableError(ResearchError):
    """Raised when an academic source is unreachable."""
    pass

class ApprovalRequiredError(ResearchError):
    """Raised when an action requires user approval."""
    pass
```

- Catch specific exceptions
- Log exceptions with full context
- Return meaningful error responses
- Never expose internal errors to API consumers
- Preserve partial state on failure

---

## Performance Guidelines

- Async everywhere (FastAPI, SQLAlchemy async, httpx)
- Connection pooling for database
- Connection pooling for Redis
- Rate limiting on external APIs
- Caching for repeated LLM calls (same paper, same analysis)
- Pagination on all list endpoints
- Lazy loading for heavy relationships
- Background tasks for non-critical operations

---

## Documentation

- Docstrings on all public functions/classes
- API endpoints documented with OpenAPI (auto from FastAPI)
- README with setup instructions
- Architecture doc for system understanding
- Data model doc for database schema
- API design doc for endpoint contracts
- Safety policy for permissions
- Development standards for this document
- Roadmap for phases and milestones
