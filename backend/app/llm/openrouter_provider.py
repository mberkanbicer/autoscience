"""OpenRouter LLM provider."""

from typing import Any

import httpx

from .base import CompletionResult, LLMProvider, Message, StructuredOutput

# OpenRouter model pricing per 1M tokens (approximate, varies by model)
OPENROUTER_PRICING = {
    "anthropic/claude-3-opus": {"input": 15.00, "output": 75.00},
    "anthropic/claude-3-sonnet": {"input": 3.00, "output": 15.00},
    "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "google/gemini-pro-1.5": {"input": 1.25, "output": 5.00},
    "meta-llama/llama-3-70b": {"input": 0.52, "output": 0.75},
    "meta-llama/llama-3-8b": {"input": 0.05, "output": 0.10},
    "mistralai/mixtral-8x7b": {"input": 0.24, "output": 0.24},
    "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28},
}


class OpenRouterProvider(LLMProvider):
    """OpenRouter LLM provider - access multiple models via OpenRouter API."""

    def __init__(
        self,
        api_key: str,
        default_model: str = "openai/gpt-4o",
        base_url: str = "https://openrouter.ai/api/v1",
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = default_model
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://autoscience.dev",
                "X-Title": "Autoscience",
            },
            timeout=120.0,
        )

    @property
    def provider_name(self) -> str:
        return "openrouter"

    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> CompletionResult:
        """Generate a completion using OpenRouter API."""
        model = model or self.default_model

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        response = await self._client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})

        cost = self.estimate_cost(
            {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            },
            model,
        )

        return CompletionResult(
            content=choice["message"]["content"] or "",
            model=model,
            provider=self.provider_name,
            usage=usage,
            cost_usd=cost,
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
        )

    async def complete_structured(
        self,
        messages: list[Message],
        schema: dict[str, Any],
        model: str | None = None,
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> StructuredOutput:
        """Generate a structured completion using OpenRouter."""
        model = model or self.default_model

        # Add schema instruction to the last message
        schema_instruction = f"\n\nRespond with valid JSON matching this schema:\n{schema}"
        modified_messages = list(messages)
        last_msg = modified_messages[-1]
        modified_messages[-1] = Message(
            role=last_msg.role,
            content=last_msg.content + schema_instruction,
        )

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in modified_messages],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

        response = await self._client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        content = choice["message"]["content"] or "{}"

        import json

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {"error": "Failed to parse JSON", "raw": content}

        usage = data.get("usage", {})
        cost = self.estimate_cost(
            {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            },
            model,
        )

        completion = CompletionResult(
            content=content,
            model=model,
            provider=self.provider_name,
            usage=usage,
            cost_usd=cost,
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
        )

        return StructuredOutput(data=parsed, completion=completion)

    def count_tokens(self, text: str) -> int:
        """Estimate token count (approximate: 1 token ≈ 4 characters)."""
        return len(text) // 4

    def estimate_cost(self, usage: dict[str, int], model: str) -> float:
        """Estimate cost in USD."""
        pricing = OPENROUTER_PRICING.get(model)
        if not pricing:
            return 0.0

        input_cost = (usage.get("prompt_tokens", 0) / 1_000_000) * pricing["input"]
        output_cost = (usage.get("completion_tokens", 0) / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 6)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
