"""Application configuration from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "autoscience"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    app_secret_key: str = "change-me-to-a-random-secret"

    # Database
    database_url: str = "postgresql+asyncpg://autoscience:autoscience@localhost:5432/autoscience"
    database_url_sync: str = "postgresql://autoscience:autoscience@localhost:5432/autoscience"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM Providers
    openai_api_key: str = ""
    openai_default_model: str = "gpt-4o"
    openai_org_id: str = ""

    anthropic_api_key: str = ""
    anthropic_default_model: str = "claude-sonnet-4-20250514"

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_default_model: str = "openai/gpt-4o"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Local LLM (Ollama or compatible)
    local_llm_base_url: str = "http://localhost:11434"
    local_llm_model: str = "llama3"

    # Llama.cpp (llama-server)
    llamacpp_base_url: str = "http://localhost:8080"
    llamacpp_model: str = "local-model"

    default_llm_provider: Literal["openai", "anthropic", "openrouter", "local", "llamacpp"] = "openai"

    # Embeddings
    embedding_provider: Literal["openai", "local"] = "openai"
    embedding_model: str = "text-embedding-3-small"
    local_embedding_url: str = "http://localhost:11434"
    local_embedding_model: str = "nomic-embed-text"

    # Academic API Keys (optional)
    semantic_scholar_api_key: str = ""
    core_api_key: str = ""
    unpaywall_email: str = "your-email@example.com"

    # SearXNG
    searxng_url: str = "https://search.bicers.me"
    searxng_categories: str = "science,general"
    searxng_engines: str = ""  # comma-separated, empty = all
    cache_ttl_seconds: int = 3600

    # Sandbox
    sandbox_docker_image: str = "autoscience-sandbox:latest"
    sandbox_timeout_seconds: int = 300
    sandbox_memory_limit: str = "512m"
    sandbox_cpu_limit: float = 1.0

    # Idle Cognition
    idle_enabled: bool = True
    idle_check_interval_minutes: int = 5

    # Budget Defaults
    default_max_cost_per_run_usd: float = 5.0
    default_max_sources_per_run: int = 50
    default_max_minutes_per_run: int = 60

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Frontend
    next_public_api_url: str = "http://localhost:8000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
