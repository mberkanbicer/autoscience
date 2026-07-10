"""Llama.cpp local LLM provider."""

from typing import Any

import httpx
import structlog

from .base import CompletionResult, LLMProvider, Message, StructuredOutput

logger = structlog.get_logger()


class LlamaCppProvider(LLMProvider):
    """Llama.cpp local LLM provider via llama-server HTTP API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        default_model: str = "local-model",
    ):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=180.0,
        )

    @property
    def provider_name(self) -> str:
        return "llamacpp"

    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> CompletionResult:
        """Generate a completion using llama-server API."""
        # llama-server supports OpenAI-compatible /v1/chat/completions
        payload = {
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": False,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        response = await self._client.post("/v1/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})

        return CompletionResult(
            content=choice["message"]["content"] or "",
            model=data.get("model", self.default_model),
            provider=self.provider_name,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            cost_usd=0.0,  # Local models are free
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
        """Generate a structured completion using llama-server."""
        # Add schema instruction to the last message
        schema_instruction = f"\n\nRespond with valid JSON matching this schema:\n{schema}"
        modified_messages = list(messages)
        last_msg = modified_messages[-1]
        modified_messages[-1] = Message(
            role=last_msg.role,
            content=last_msg.content + schema_instruction,
        )

        payload = {
            "messages": [{"role": m.role, "content": m.content} for m in modified_messages],
            "temperature": temperature,
            "stream": False,
        }

        response = await self._client.post("/v1/chat/completions", json=payload)
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

        completion = CompletionResult(
            content=content,
            model=data.get("model", self.default_model),
            provider=self.provider_name,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            cost_usd=0.0,
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
        )

        return StructuredOutput(data=parsed, completion=completion)

    def count_tokens(self, text: str) -> int:
        """Estimate token count (approximate: 1 token ≈ 4 characters)."""
        return len(text) // 4

    async def health_check(self) -> bool:
        """Check if llama-server is running."""
        try:
            response = await self._client.get("/health")
            return response.status_code == 200
        except httpx.RequestError:
            return False
        except Exception as exc:
            logger.warning("health_check_failed", error=str(exc))
            return False

    async def get_models(self) -> list[dict[str, Any]]:
        """Get available models from llama-server."""
        try:
            response = await self._client.get("/v1/models")
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except httpx.RequestError:
            return []
        except Exception as exc:
            logger.warning("get_models_failed", error=str(exc))
            return []

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
