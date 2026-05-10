"""Base provider interface for all LLM providers.

Every provider (Ollama, OpenAI, Anthropic, etc.) implements this interface.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatMessage:
    """A single message in a chat conversation."""

    role: str  # system | user | assistant | tool
    content: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_call_id: str = ""
    name: str = ""


@dataclass
class ChatResponse:
    """Response from a chat completion call."""

    content: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = ""

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


@dataclass
class EmbeddingResponse:
    """Response from an embedding call."""

    embedding: list[float] = field(default_factory=list)
    model: str = ""
    input_tokens: int = 0


class BaseProvider(abc.ABC):
    """Abstract base for all LLM providers.

    Every provider must implement:
    - is_available(): Check if the provider is reachable
    - chat(): Send a chat completion request
    - embed(): Generate embeddings (optional)
    """

    provider_name: str = "base"

    @abc.abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is reachable and ready."""
        ...

    @abc.abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        tools: list[dict[str, Any]] | None = None,
        timeout: float = 120.0,
    ) -> ChatResponse:
        """Send a chat completion request.

        Args:
            messages: Conversation history.
            model: Model name/identifier.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            tools: Tool/function definitions (optional).
            timeout: Request timeout in seconds.

        Returns:
            ChatResponse with generated content and token counts.
        """
        ...

    async def embed(
        self,
        text: str,
        model: str,
    ) -> EmbeddingResponse:
        """Generate an embedding for text.

        Default implementation raises NotImplementedError.
        Override in providers that support embeddings.
        """
        raise NotImplementedError(f"{self.provider_name} does not support embeddings")

    async def list_models(self) -> list[str]:
        """List available models from this provider.

        Default returns empty list. Override in providers that support listing.
        """
        return []
