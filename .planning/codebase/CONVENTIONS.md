# Coding Conventions

**Analysis Date:** 2026-07-09

## Naming Patterns

**Files:**
- snake_case for Python backend files (`project_service.py`, `skill_performance_service.py`)
- PascalCase for TypeScript/React components (`SkillEvalSettings.tsx`, `SkillPerformancePanel.tsx`)
- kebab-case for frontend pages (`project-form.tsx`, `use-skill-eval-stream.ts` for hooks)

**Functions:**
- snake_case in Python (`create_project`, `evaluate_all_skills`, `get_scheduler_config`)
- camelCase in TypeScript (`runResearch`, `handleToggle`, `updateSchedulerConfig`)

**Variables:**
- snake_case in Python (local and module variables)
- camelCase in TypeScript (including hooks like `useSkillEvalStream`)

**Types:**
- PascalCase in TypeScript interfaces (`SkillEvalHistoryEntry`, `SkillPerformanceStats`)
- PascalCase in Python classes (`SkillPerformanceService`, `EventBroadcaster`)

**Constants:**
- UPPER_SNAKE_CASE in Python (`SYSTEM_EVAL_CHANNEL`, `MIN_SUCCESS_RATE`)
- UPPER_SNAKE_CASE in TypeScript (`AUTH_TOKEN_KEY`, `HOUR_OPTIONS`)

## Code Style

**Formatting:**
- Python: ruff with line-length 100 (`backend/pyproject.toml`)
- TypeScript: prettier via Next.js default config

**Linting:**
- Python: `ruff check` with rules `["E", "F", "I", "N", "W", "UP"]`
- TypeScript: `tsc --noEmit` for type checking (no eslint configured)
- E2E: TypeScript via Playwright config

## Import Organization

**Order (Python):**
1. Standard library imports (`from __future__ import annotations`, `import asyncio`)
2. Third-party imports (`import structlog`, `from fastapi import ...`)
3. Local application imports (`from ..config import get_settings`)

**Order (TypeScript):**
1. React/hooks imports
2. Library imports (`lucide-react`, `next/navigation`)
3. Local imports (`@/lib/api`, `@/components/ui/Card`)
4. Type imports (`import type { Skill } from '@/lib/types'`)

**Path Aliases:**
- Frontend: `@/` maps to `frontend/src/` (Next.js alias)
- Backend: No aliases; uses relative imports (`from ..services.x import Y`)

## Error Handling

**Backend:**
- try/except with structlog logging at every layer
- Errors accumulated in result objects (e.g., `PerformanceEvaluationResult.errors`)
- Graceful degradation: failed steps don't crash the workflow
- Fire-and-forget pattern for non-critical operations (SSE broadcast)
```python
try:
    result = await service.evaluate_all_skills(...)
except Exception as e:
    logger.error("evaluation_failed", error=str(e))
    errors.append(str(e))
```

**Frontend:**
- try/catch in API calls with user-facing error messages
- Error states handled per-component (loading/error/data ternary)
- Console.error for debugging, setError for user feedback
```typescript
try {
  const data = await skillsApi.evalHistory({ limit: 50 });
  setEntries(data);
} catch (e) {
  setError('Failed to load evaluation history');
}
```

## Logging

**Framework:** structlog (Python only)

**Patterns:**
```python
import structlog
logger = structlog.get_logger()

logger.info("eval_scheduler_started", interval_hours=interval_hours, dry_run=dry_run)
logger.error("api_call_failed", endpoint="/api/v1/projects", error=str(e))
```

**Frontend:** No structured logging; uses `console.error` for debugging

## State Management

**Backend (module-level state):**
- Scheduler state stored as module-level globals (`_scheduler_task`, `_runtime_config`)
- DB session created per-operation via factory (`async with db_factory() as db:`)
- Runtime config mutable via API and persisted in memory

**Frontend (component state):**
- `useState` for local component state
- `useCallback` for stable function references in effects
- Staged changes pattern (dirty flag + apply button) for settings

## Hook Design

**Pattern:**
```typescript
// Hooks encapsulate side effects and return state/functions
export function useSkillEvalStream() {
  const { addToast } = useToast();
  useEffect(() => {
    const eventSource = new EventSource('/api/v1/skills/performance/eval-stream');
    eventSource.onmessage = (event) => { ... };
    return () => eventSource.close();
  }, []);
}
```

## Component Design

**Pattern:**
- Client components with `'use client'` directive
- Props interface defined above component
- Named exports (not default)
- Consistent className prop for parent styling
- Loading, empty, error states handled explicitly

```typescript
'use client';

interface Props {
  className?: string;
}

export function SkillEvalSettings({ className }: Props) {
  // Loading state
  if (loading) return <Card>...</Card>;
  // Error state
  if (error) return <Card>...</Card>;
  // Empty state
  if (entries.length === 0) return <Card>...</Card>;
  // Data state
  return <Card>...</Card>;
}
```

## Design System Conventions

- Tailwind CSS with custom HSL variables (defined in `globals.css`)
- Amber/Sage color palette (primary/warning/success/info/error)
- glass morphism: `bg-muted/20 backdrop-blur-xl border border-border/5`
- compact text: `text-[10px] font-black uppercase tracking-widest` for labels
- Shadow/glow: `shadow-inner`, `shadow-lg` for depth
- Transitions: `transition-all duration-300`, `hover:scale-[1.02]`
- Badge variants: `success`, `warning`, `danger`, `info`, `default`

*Convention analysis: 2026-07-09*
