"""LLM provider router for selecting and managing providers."""

import structlog
from typing import Any

from .base import LLMProvider, Message, CompletionResult, StructuredOutput
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .local_provider import LocalProvider
from .openrouter_provider import OpenRouterProvider
from .llamacpp_provider import LlamaCppProvider

logger = structlog.get_logger()


class LLMRouter:
    """Router for managing multiple LLM providers with fallback support."""

    def __init__(self, providers: dict[str, LLMProvider] | None = None):
        self.providers: dict[str, LLMProvider] = providers or {}
        self.default_provider: str | None = None
        self.fallback_chain: list[str] = []

    def register_provider(self, name: str, provider: LLMProvider) -> None:
        """Register a provider."""
        self.providers[name] = provider
        logger.info("provider_registered", provider=name)

    def set_default(self, name: str) -> None:
        """Set the default provider."""
        if name not in self.providers:
            raise ValueError(f"Provider {name} not registered")
        self.default_provider = name

    def set_fallback_chain(self, chain: list[str]) -> None:
        """Set the fallback chain order."""
        self.fallback_chain = chain

    def get_provider(self, name: str | None = None) -> LLMProvider:
        """Get a provider by name, or the default if not specified."""
        provider_name = name or self.default_provider
        if not provider_name:
            raise ValueError("No provider specified and no default set")
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not registered")
        return self.providers[provider_name]

    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        provider: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> CompletionResult:
        """Generate a completion with automatic fallback."""
        # Try primary provider first
        try:
            p = self.get_provider(provider)
            result = await p.complete(
                messages, model=model, temperature=temperature, max_tokens=max_tokens, **kwargs
            )
            logger.info(
                "completion_success",
                provider=p.provider_name,
                model=result.model,
                tokens=result.usage.get("total_tokens", 0),
                cost=result.cost_usd,
            )
            return result
        except Exception as e:
            logger.error("completion_failed", provider=provider, error=str(e))

            # Try fallback providers
            for fallback_name in self.fallback_chain:
                if fallback_name == provider:
                    continue
                if fallback_name not in self.providers:
                    continue

                try:
                    p = self.providers[fallback_name]
                    result = await p.complete(
                        messages,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs,
                    )
                    logger.info(
                        "completion_fallback_success",
                        provider=fallback_name,
                        model=result.model,
                    )
                    return result
                except Exception as fallback_error:
                    logger.error(
                        "fallback_failed",
                        provider=fallback_name,
                        error=str(fallback_error),
                    )

            # All providers failed
            raise RuntimeError(f"All LLM providers failed. Last error: {e}")

    async def complete_structured(
        self,
        messages: list[Message],
        schema: dict[str, Any],
        model: str | None = None,
        provider: str | None = None,
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> StructuredOutput:
        """Generate a structured completion with automatic fallback."""
        try:
            p = self.get_provider(provider)
            return await p.complete_structured(
                messages, schema=schema, model=model, temperature=temperature, **kwargs
            )
        except Exception as e:
            logger.error("structured_completion_failed", provider=provider, error=str(e))

            # Try fallback providers
            for fallback_name in self.fallback_chain:
                if fallback_name == provider:
                    continue
                if fallback_name not in self.providers:
                    continue

                try:
                    p = self.providers[fallback_name]
                    return await p.complete_structured(
                        messages,
                        schema=schema,
                        model=model,
                        temperature=temperature,
                        **kwargs,
                    )
                except Exception as fallback_error:
                    logger.error(
                        "structured_fallback_failed",
                        provider=fallback_name,
                        error=str(fallback_error),
                    )

            raise RuntimeError(f"All LLM providers failed. Last error: {e}")

    def count_tokens(self, text: str, provider: str | None = None) -> int:
        """Count tokens using a provider's estimator."""
        p = self.get_provider(provider)
        return p.count_tokens(text)

    async def health_check(self) -> dict[str, bool]:
        """Check health of all registered providers."""
        results = {}
        for name, provider in self.providers.items():
            if isinstance(provider, LocalProvider):
                results[name] = await provider.health_check()
            else:
                # For cloud providers, assume healthy if configured
                results[name] = True
        return results


def create_default_router(
    openai_api_key: str | None = None,
    anthropic_api_key: str | None = None,
    openrouter_api_key: str | None = None,
    openrouter_default_model: str | None = None,
    openrouter_base_url: str | None = None,
    local_base_url: str | None = None,
    local_model: str | None = None,
    llamacpp_base_url: str | None = None,
    llamacpp_model: str | None = None,
    default_provider: str = "openai",
) -> LLMRouter:
    """Create a router with configured providers."""
    router = LLMRouter()

    if openai_api_key:
        router.register_provider(
            "openai",
            OpenAIProvider(api_key=openai_api_key),
        )

    if anthropic_api_key:
        router.register_provider(
            "anthropic",
            AnthropicProvider(api_key=anthropic_api_key),
        )

    if openrouter_api_key:
        router.register_provider(
            "openrouter",
            OpenRouterProvider(
                api_key=openrouter_api_key,
                default_model=openrouter_default_model or "openai/gpt-4o",
                base_url=openrouter_base_url or "https://openrouter.ai/api/v1",
            ),
        )

    if local_base_url:
        router.register_provider(
            "local",
            LocalProvider(base_url=local_base_url, model=local_model or "llama3"),
        )

    if llamacpp_base_url:
        router.register_provider(
            "llamacpp",
            LlamaCppProvider(
                base_url=llamacpp_base_url,
                default_model=llamacpp_model or "local-model",
            ),
        )

    # Set default and fallback chain
    available = list(router.providers.keys())
    if default_provider in available:
        router.set_default(default_provider)
        fallback = [p for p in available if p != default_provider]
        router.set_fallback_chain(fallback)

    return router
