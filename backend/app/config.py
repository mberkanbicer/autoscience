"""Application configuration from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "autoscience"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    app_secret_key: str = "change-me-to-a-random-secret"
    jwt_expire_hours: int = 72

    # API Authentication
    api_key: str = ""

    # SMTP notifications (optional)
    notification_email_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@autoscience.local"
    smtp_use_tls: bool = True

    # OAuth (optional — enables Google/GitHub login)
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    github_oauth_client_id: str = ""
    github_oauth_client_secret: str = ""
    oauth_redirect_uri: str = "http://localhost:3000/auth/callback"

    # Database
    database_url: str = "postgresql+asyncpg://autoscience:autoscience@localhost:5432/autoscience"
    database_url_sync: str = "postgresql://autoscience:autoscience@localhost:5432/autoscience"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    # Comma-separated cluster nodes (host:port or redis:// URLs). When set, cluster mode is used.
    redis_cluster_nodes: str = ""

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
    firecrawl_api_key: str = ""

    # Kaggle (optional — enables dataset search)
    kaggle_username: str = ""
    kaggle_key: str = ""

    # SearXNG (leave empty to disable the SearXNG connector)
    searxng_url: str = ""
    searxng_categories: str = "science,general"
    searxng_engines: str = ""
    cache_ttl_seconds: int = 3600

    # Sandbox
    sandbox_docker_image: str = "autoscience-sandbox:latest"
    sandbox_timeout_seconds: int = 300
    sandbox_memory_limit: str = "512m"
    sandbox_cpu_limit: float = 1.0

    # Health Monitor
    health_check_enabled: bool = True
    health_check_interval_minutes: int = 5

    # Idle Cognition
    idle_enabled: bool = True
    idle_check_interval_minutes: int = 5

    # Skill Evaluation Scheduler
    skill_eval_enabled: bool = True
    skill_eval_interval_hours: int = 24
    skill_eval_dry_run: bool = False  # When True, evaluates but never mutates

    # Budget Defaults
    default_max_cost_per_run_usd: float = 5.0
    default_max_sources_per_run: int = 50
    default_max_minutes_per_run: int = 60

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Frontend
    next_public_api_url: str = "http://localhost:8000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @model_validator(mode="after")
    def _validate_security(self) -> "Settings":
        """Fail closed in non-development environments.

        Production/staging must set a strong ``app_secret_key`` and an ``api_key``.
        """
        if self.app_env == "development":
            return self
        if not self.app_secret_key or self.app_secret_key == "change-me-to-a-random-secret":
            raise ValueError(
                "app_secret_key must be set to a strong random value "
                "when app_env is not 'development'"
            )
        if not self.api_key:
            raise ValueError(
                "api_key must be configured when app_env is not 'development'"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
