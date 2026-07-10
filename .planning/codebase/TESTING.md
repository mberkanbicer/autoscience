# Testing Patterns

**Analysis Date:** 2026-07-09

## Test Frameworks

### Backend (Python)
**Runner:** pytest 8.0+ via `pytest`
**Config:** `backend/pyproject.toml`
**Async:** pytest-asyncio for async test support
**Parallel:** pytest-xdist (optional)

### Frontend (TypeScript)
**Runner:** vitest via `npx vitest`
**Config:** `frontend/vitest.config.ts`
**E2E:** Playwright via `npx playwright test`
**Config:** `frontend/playwright.config.ts`

## Run Commands

```bash
# Backend
cd backend && pytest                          # Run all tests
cd backend && pytest -x                       # Stop on first failure
cd backend && pytest --cov=app                # Run with coverage
cd backend && pytest -n auto                  # Parallel (if xdist installed)
cd backend && pytest tests/test_services/     # Run specific test directory

# Frontend
cd frontend && npx vitest run                 # Run frontend unit tests
cd frontend && npx playwright test            # Run E2E tests
cd frontend && npx vitest                     # Watch mode

# TypeScript type checking
cd frontend && npx tsc --noEmit               # TypeScript compile check
```

## Test File Organization

### Backend (`backend/tests/`)
```
backend/tests/
├── conftest.py                 # Shared fixtures
├── test_api/                   # API endpoint tests
│   ├── test_projects.py
│   ├── test_ideas.py
│   └── ...
├── test_services/              # Service-level tests
│   ├── test_skill_evaluation_scheduler.py
│   ├── test_knowledge_service.py
│   ├── test_research_persistence.py
│   ├── test_notebook_export.py
│   ├── test_notification_service.py
│   ├── test_manuscript_context.py
│   ├── test_user_activity_service.py
│   ├── test_wiki_embedding.py
│   ├── test_snapshot_service.py
│   ├── test_idle_scheduler_lock.py
│   └── ...
├── test_workflows/
│   ├── test_workflow.py
│   ├── test_flexible_workflow.py
│   └── test_safety_gates.py
├── test_engine/
├── test_engines/
├── test_models/
├── test_connectors/
├── test_agents/
├── test_llm/
├── test_migrations/
└── test_integration/
```

### Frontend (`frontend/`)
```
frontend/
├── e2e/
│   └── smoke.spec.ts           # Playwright E2E smoke test
└── src/lib/
    └── __tests__/
        └── settingsVault.test.ts  # vitest unit test
```

## Test Patterns

### Backend API Test
```python
@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    response = await client.post("/api/v1/projects", json={"name": "Test", ...})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test"
```

### Backend Service Test
```python
@pytest.mark.asyncio
async def test_evaluate_all_skills(service: SkillPerformanceService):
    result = await service.evaluate_all_skills(dry_run=True)
    assert result.evaluated_count >= 0
    assert isinstance(result.summary, str)
```

### Backend Mocking
```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_literature_search():
    mock_connector = AsyncMock()
    mock_connector.search.return_value = SearchResult(...)
    with patch("app.connectors.manager.ConnectorManager") as MockManager:
        manager = MockManager.return_value
        # Test with mocked connector
```

### Frontend vitest Test
```typescript
import { describe, it, expect } from 'vitest';
import { encryptKey, decryptKey } from '@/lib/settingsVault';

describe('settingsVault', () => {
  it('encrypts and decrypts an API key', () => {
    const key = 'sk-test-12345';
    const encrypted = encryptKey(key, 'password');
    const decrypted = decryptKey(encrypted, 'password');
    expect(decrypted).toBe(key);
  });
});
```

### Frontend Playwright E2E
```typescript
import { test, expect } from '@playwright/test';

test('project page loads for created project', async ({ page }) => {
  await page.goto('http://localhost:3000/projects/test-id');
  await expect(page.locator('h1')).toContainText('Research Skills');
});
```

## Mocking

**Backend:**
- AsyncMock for external API calls (arXiv, Semantic Scholar)
- Patch for LLM provider responses
- Database fixtures with function-scoped transactions
- Redis unavailable gracefully handled (no mock needed)

**Frontend:**
- API calls mocked at the fetch level (vitest)
- Playwright tests use a running dev server + proxied backend

## Coverage

**No enforced threshold** in either backend or frontend config.

View coverage:
```bash
# Backend
pytest --cov=app --cov-report=html

# Frontend
npx vitest run --coverage
```

## Key Test Considerations

- **Redis-dependent tests:** SSE endpoints require Redis. Tests gracefully degrade when Redis is unavailable.
- **Database state:** Tests use a test database. Each test is wrapped in a transaction that rolls back on teardown.
- **LLM-dependent tests:** Tests mock LLM responses. No real API calls in CI.
- **E2E:** Playwright tests require both frontend and backend running. The E2E setup script (`frontend/scripts/e2e-server.sh`) handles this.
- **TypeScript:** Run `npx tsc --noEmit` for type checking before committing.

*Testing analysis: 2026-07-09*
