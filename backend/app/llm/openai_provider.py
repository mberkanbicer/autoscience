"""OpenAI LLM provider."""

from typing import Any

from openai import AsyncOpenAI

from .base import CompletionResult, LLMProvider, Message, StructuredOutput

# Model pricing per 1M tokens (as of 2025)
MODEL_PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "o3-mini": {"input": 1.10, "output": 4.40},
    "o3": {"input": 10.00, "output": 40.00},
    "text-embedding-3-small": {"input": 0.02, "output": 0.0},
    "text-embedding-3-large": {"input": 0.13, "output": 0.0},
}


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(
        self,
        api_key: str,
        org_id: str | None = None,
        default_model: str = "gpt-4o",
    ):
        self.client = AsyncOpenAI(api_key=api_key, org_id=org_id)
        self.default_model = default_model

    @property
    def provider_name(self) -> str:
        return "openai"

    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> CompletionResult:
        """Generate a completion using OpenAI API."""
        model = model or self.default_model

        openai_messages = [{"role": m.role, "content": m.content} for m in messages]

        response = await self.client.chat.completions.create(
            model=model,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        choice = response.choices[0]
        usage = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        }

        cost = self.estimate_cost(usage, model)

        return CompletionResult(
            content=choice.message.content or "",
            model=model,
            provider=self.provider_name,
            usage=usage,
            cost_usd=cost,
            finish_reason=choice.finish_reason,
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
        """Generate a structured completion using OpenAI's response_format."""
        model = model or self.default_model

        # For structured output, we use JSON mode and parse
        openai_messages = [{"role": m.role, "content": m.content} for m in messages]

        # Add instruction to output valid JSON matching schema
        schema_instruction = f"\n\nYou must respond with valid JSON matching this schema:\n{schema}"
        openai_messages[-1]["content"] += schema_instruction

        response = await self.client.chat.completions.create(
            model=model,
            messages=openai_messages,
            temperature=temperature,
            response_format={"type": "json_object"},
            **kwargs,
        )

        choice = response.choices[0]
        content = choice.message.content or "{}"

        from app.utils.json_utils import parse_llm_json
        data = parse_llm_json(content)

        usage = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        }

        cost = self.estimate_cost(usage, model)

        return StructuredOutput(
            data=data,
            model=model,
            usage=usage,
            cost_usd=cost,
            finish_reason=choice.finish_reason,
            raw_response=response,
        )

        return StructuredOutput(data=data, completion=completion)

    def count_tokens(self, text: str) -> int:
        """Estimate token count (approximate: 1 token ≈ 4 characters)."""
        return len(text) // 4

    def estimate_cost(self, usage: dict[str, int], model: str) -> float:
        """Estimate cost in USD."""
        pricing = MODEL_PRICING.get(model)
        if not pricing:
            return 0.0

        input_cost = (usage.get("prompt_tokens", 0) / 1_000_000) * pricing["input"]
        output_cost = (usage.get("completion_tokens", 0) / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 6)

    async def embed(self, texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
        """Generate embeddings for texts."""
        response = await self.client.embeddings.create(
            model=model,
            input=texts,
        )
        return [item.embedding for item in response.data]
