# Troubleshooting Guide

## Common Issues

### Backend won't start
```bash
# Check logs
docker compose -f docker/docker-compose.dev.yml logs backend

# Most common cause: import error
# Fix by running the dev install command:
docker compose -f docker/docker-compose.dev.yml exec backend pip install -e . --quiet
```

### Frontend shows "Waiting for search events..."
1. Check the browser console for SSE connection errors
2. Verify Redis is running: `docker compose ps redis`
3. Check backend logs for Redis connection errors
4. The SSE endpoint auto-reconnects, but events only arrive for active runs

### Research run stuck in "created" state
Old runs started before a commit fix may never transition to "running". Delete and re-create:
```bash
curl -X DELETE http://localhost:8000/api/v1/runs/{run_id}
```

### Redis connection refused
- Docker: ensure `REDIS_URL=redis://redis:6379/0` is set in backend env
- Local dev: ensure Redis is running on port 6380 (mapped to 6379)
- Check `docker compose ps redis`

### API key not working
- Set keys in the frontend Settings page (stored in localStorage)
- Sent as headers: `X-OpenRouter-API-Key`, `X-Default-Provider`
- Check browser devtools Network tab for the request headers

### Database migration issues
```bash
# Generate a new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Apply pending migrations
docker compose exec backend alembic upgrade head
```

### PostgreSQL connection error
- Verify PostgreSQL is running: `docker compose ps db`
- Check `DATABASE_URL` in backend env matches Docker compose config
- Default dev: `postgresql+asyncpg://autoscience:autoscience@localhost:5433/autoscience`

## API Key Configuration Guide

### OpenRouter (Recommended)
1. Sign up at https://openrouter.ai
2. Generate an API key
3. In the frontend Settings page, enter your OpenRouter API key
4. Select model: `openai/gpt-4o`, `anthropic/claude-sonnet-4`, or `google/gemini-2.5-pro`

### OpenAI
1. Get key from https://platform.openai.com/api-keys
2. Set in Settings or `.env`: `OPENAI_API_KEY=sk-...`
3. Set `DEFAULT_LLM_PROVIDER=openai`

### Anthropic
1. Get key from https://console.anthropic.com
2. Set in Settings or `.env`: `ANTHROPIC_API_KEY=sk-ant-...`
3. Set `DEFAULT_LLM_PROVIDER=anthropic`

### Local Models (Ollama)
1. Install Ollama: https://ollama.ai
2. Pull a model: `ollama pull llama3`
3. Set environment: `LOCAL_LLM_BASE_URL=http://localhost:11434`
4. Set `DEFAULT_LLM_PROVIDER=local`

## Developer Documentation

### Project Structure
```
autoscience/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── agents/       # LLM agent definitions
│   │   ├── connectors/   # Academic source connectors
│   │   ├── engine/       # Research engines
│   │   ├── llm/          # LLM provider abstraction
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic validation schemas
│   │   ├── services/     # Business logic services
│   │   └── workflows/    # Research workflow engine
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/          # Next.js pages
│       ├── components/   # React components
│       └── lib/          # API client and types
└── docker/
```

### Adding a New Engine
1. Create `backend/app/engine/new_engine.py`
2. Implement the engine class with LLM support + fallback
3. Add to `orchestrator.py` constructor
4. Wire into `research_workflow.py`
5. Add `_execute_step` call in `_run_user_directed`

### Adding a New API Endpoint
1. Create `backend/app/api/new_resource.py`
2. Define Pydantic schemas in `backend/app/schemas/`
3. Register router in `backend/app/api/router.py`
4. Add frontend API client method in `frontend/src/lib/api.ts`
5. Add TypeScript types in `frontend/src/lib/types.ts`
6. Create frontend page if needed

### Running Tests
```bash
# All tests
cd backend && python -m pytest

# Specific test file
python -m pytest tests/test_engine/ -v

# With coverage
python -m pytest --cov=app tests/
```

### Code Style
```bash
cd backend
ruff check .
ruff format .
```
