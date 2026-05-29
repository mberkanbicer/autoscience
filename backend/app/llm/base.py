"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    """A message in a conversation."""

    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class CompletionResult:
    """Result from an LLM completion."""

    content: str
    model: str
    provider: str
    usage: dict[str, int] = field(default_factory=dict)  # prompt_tokens, completion_tokens, total_tokens
    cost_usd: float = 0.0
    finish_reason: str | None = None
    raw_response: Any = None


@dataclass
class StructuredOutput:
    """Result from structured output completion."""

    data: dict[str, Any]
    completion: CompletionResult


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        ...

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> CompletionResult:
        """Generate a completion from messages."""
        ...

    @abstractmethod
    async def complete_structured(
        self,
        messages: list[Message],
        schema: dict[str, Any],
        model: str | None = None,
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> StructuredOutput:
        """Generate a structured completion matching a JSON schema."""
        ...

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        ...

    def estimate_cost(self, usage: dict[str, int], model: str) -> float:
        """Estimate cost in USD for a completion. Override in subclasses."""
        return 0.0

    def format_messages(
        self,
        system_prompt: str | None = None,
        user_message: str = "",
        history: list[Message] | None = None,
    ) -> list[Message]:
        """Helper to format messages with optional system prompt and history."""
        messages = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        if history:
            messages.extend(history)
        messages.append(Message(role="user", content=user_message))
        return messages
