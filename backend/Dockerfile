FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi>=0.110.0 \
    uvicorn[standard]>=0.27.0 \
    python-multipart>=0.0.9 \
    sqlalchemy[asyncio]>=2.0.25 \
    asyncpg>=0.29.0 \
    psycopg2-binary>=2.9.9 \
    redis>=5.0.0 \
    pydantic>=2.5.0 \
    pydantic-settings>=2.1.0 \
    openai>=1.12.0 \
    anthropic>=0.18.0 \
    httpx>=0.27.0 \
    structlog>=24.1.0 \
    python-dotenv>=1.0.0 \
    apscheduler>=3.10.4 \
    alembic>=1.13.0 \
    pgvector>=0.2.4 \
    sentence-transformers>=2.3.0 \
    scikit-learn>=1.4.0 \
    pandas>=2.2.0 \
    matplotlib>=3.8.0 \
    aiosqlite>=0.20.0

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application with migrations
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
