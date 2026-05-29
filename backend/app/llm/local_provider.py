"""Local LLM provider (Ollama, vLLM, etc.)."""

from typing import Any

import httpx

from .base import LLMProvider, Message, CompletionResult, StructuredOutput


class LocalProvider(LLMProvider):
    """Local LLM provider supporting Ollama and vLLM APIs."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
        api_format: str = "ollama",  # "ollama" or "openai"
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_format = api_format
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)

    @property
    def provider_name(self) -> str:
        return "local"

    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> CompletionResult:
        """Generate a completion using local LLM."""
        model = model or self.model

        if self.api_format == "ollama":
            return await self._complete_ollama(messages, model, temperature, max_tokens)
        else:
            return await self._complete_openai_compat(messages, model, temperature, max_tokens)

    async def _complete_ollama(
        self,
        messages: list[Message],
        model: str,
        temperature: float,
        max_tokens: int | None,
    ) -> CompletionResult:
        """Complete using Ollama API format."""
        ollama_messages = [{"role": m.role, "content": m.content} for m in messages]

        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        response = await self.client.post("/api/chat", json=payload)
        response.raise_for_status()

        data = response.json()
        content = data.get("message", {}).get("content", "")

        # Ollama provides token counts
        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
            "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
        }

        return CompletionResult(
            content=content,
            model=model,
            provider=self.provider_name,
            usage=usage,
            cost_usd=0.0,  # Local models have no API cost
            finish_reason="stop",
            raw_response=data,
        )

    async def _complete_openai_compat(
        self,
        messages: list[Message],
        model: str,
        temperature: float,
        max_tokens: int | None,
    ) -> CompletionResult:
        """Complete using OpenAI-compatible API (vLLM, etc.)."""
        openai_messages = [{"role": m.role, "content": m.content} for m in messages]

        payload: dict[str, Any] = {
            "model": model,
            "messages": openai_messages,
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        response = await self.client.post("/v1/chat/completions", json=payload)
        response.raise_for_status()

        data = response.json()
        choice = data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")

        usage_data = data.get("usage", {})
        usage = {
            "prompt_tokens": usage_data.get("prompt_tokens", 0),
            "completion_tokens": usage_data.get("completion_tokens", 0),
            "total_tokens": usage_data.get("total_tokens", 0),
        }

        return CompletionResult(
            content=content,
            model=model,
            provider=self.provider_name,
            usage=usage,
            cost_usd=0.0,
            finish_reason=choice.get("finish_reason", "stop"),
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
        """Generate a structured completion."""
        model = model or self.model

        # Add JSON schema instruction to last message
        schema_instruction = f"\n\nYou must respond with valid JSON matching this schema:\n{schema}"
        modified_messages = list(messages)
        if modified_messages:
            last_msg = modified_messages[-1]
            modified_messages[-1] = Message(
                role=last_msg.role,
                content=last_msg.content + schema_instruction,
            )

        completion = await self.complete(
            modified_messages, model=model, temperature=temperature, **kwargs
        )

        import json

        try:
            data = json.loads(completion.content)
        except json.JSONDecodeError:
            data = {"error": "Failed to parse JSON", "raw": completion.content}

        return StructuredOutput(data=data, completion=completion)

    def count_tokens(self, text: str) -> int:
        """Estimate token count (approximate)."""
        return len(text) // 4

    async def list_models(self) -> list[str]:
        """List available models from Ollama."""
        if self.api_format != "ollama":
            return [self.model]

        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception:
            return [self.model]

    async def health_check(self) -> bool:
        """Check if the local LLM server is running."""
        try:
            if self.api_format == "ollama":
                response = await self.client.get("/api/tags")
            else:
                response = await self.client.get("/v1/models")
            return response.status_code == 200
        except Exception:
            return False
