"""Anthropic LLM provider."""

from typing import Any

import anthropic
from anthropic import AsyncAnthropic

from .base import LLMProvider, Message, CompletionResult, StructuredOutput

# Model pricing per 1M tokens (as of 2025)
MODEL_PRICING = {
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
}


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider."""

    def __init__(
        self,
        api_key: str,
        default_model: str = "claude-sonnet-4-20250514",
    ):
        self.client = AsyncAnthropic(api_key=api_key)
        self.default_model = default_model

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> CompletionResult:
        """Generate a completion using Anthropic API."""
        model = model or self.default_model

        # Extract system message if present
        system_prompt = None
        anthropic_messages = []

        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                anthropic_messages.append({"role": m.role, "content": m.content})

        # Anthropic requires at least one message
        if not anthropic_messages:
            anthropic_messages.append({"role": "user", "content": "Hello"})

        # Build kwargs
        api_kwargs: dict[str, Any] = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
        }

        if system_prompt:
            api_kwargs["system"] = system_prompt

        response = await self.client.messages.create(**api_kwargs)

        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        usage = {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        }

        cost = self.estimate_cost(usage, model)

        return CompletionResult(
            content=content,
            model=model,
            provider=self.provider_name,
            usage=usage,
            cost_usd=cost,
            finish_reason=response.stop_reason,
            raw_response=response,
        )

    async def complete_structured(
        self,
        messages: list[Message],
        schema: dict[str, Any],
        model: str | None = None,
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> StructuredOutput:
        """Generate a structured completion using Anthropic API."""
        model = model or self.default_model

        # Extract system message if present
        system_prompt = None
        anthropic_messages = []

        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                anthropic_messages.append({"role": m.role, "content": m.content})

        # Add JSON schema instruction to last message
        schema_instruction = f"\n\nYou must respond with valid JSON matching this schema:\n{schema}"
        if anthropic_messages:
            anthropic_messages[-1]["content"] += schema_instruction

        # Build kwargs
        api_kwargs: dict[str, Any] = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": 4096,
        }

        if system_prompt:
            api_kwargs["system"] = system_prompt

        response = await self.client.messages.create(**api_kwargs)

        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        import json

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = {"error": "Failed to parse JSON", "raw": content}

        usage = {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        }

        cost = self.estimate_cost(usage, model)

        completion = CompletionResult(
            content=content,
            model=model,
            provider=self.provider_name,
            usage=usage,
            cost_usd=cost,
            finish_reason=response.stop_reason,
            raw_response=response,
        )

        return StructuredOutput(data=data, completion=completion)

    def count_tokens(self, text: str) -> int:
        """Estimate token count (approximate: 1 token ≈ 3.5 characters for Claude)."""
        return len(text) // 3

    def estimate_cost(self, usage: dict[str, int], model: str) -> float:
        """Estimate cost in USD."""
        pricing = MODEL_PRICING.get(model)
        if not pricing:
            return 0.0

        input_cost = (usage.get("prompt_tokens", 0) / 1_000_000) * pricing["input"]
        output_cost = (usage.get("completion_tokens", 0) / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 6)
