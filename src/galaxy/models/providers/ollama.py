"""Ollama LLM provider.

Primary provider for local model inference. Communicates with Ollama's HTTP API.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from galaxy.core.constants import DEFAULT_OLLAMA_HOST
from galaxy.core.exceptions import ModelInferenceError, ModelNotAvailableError
from galaxy.models.providers import BaseProvider, ChatMessage, ChatResponse, EmbeddingResponse

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    """Ollama local model provider."""

    provider_name = "ollama"

    def __init__(self, base_url: str = DEFAULT_OLLAMA_HOST, timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    async def list_models(self) -> list[str]:
        """List models available in Ollama."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.warning("Failed to list Ollama models: %s", e)
            return []

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        tools: list[dict[str, Any]] | None = None,
        timeout: float = 120.0,
    ) -> ChatResponse:
        """Send chat completion to Ollama."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if tools:
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

            message = data.get("message", {})
            return ChatResponse(
                content=message.get("content", ""),
                tool_calls=message.get("tool_calls", []),
                model=data.get("model", model),
                input_tokens=data.get("prompt_eval_count", 0),
                output_tokens=data.get("eval_count", 0),
                total_tokens=(
                    data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                ),
                finish_reason="stop",
            )

        except httpx.ConnectError:
            raise ModelNotAvailableError(
                model, provider="ollama",
                message=f"Cannot connect to Ollama at {self.base_url}",
            )
        except httpx.TimeoutException:
            raise ModelInferenceError(f"Ollama request timed out after {timeout}s")
        except httpx.HTTPStatusError as e:
            raise ModelInferenceError(
                f"Ollama returned {e.response.status_code}: {e.response.text[:200]}"
            )
        except Exception as e:
            raise ModelInferenceError(f"Ollama inference failed: {e}") from e

    async def embed(self, text: str, model: str) -> EmbeddingResponse:
        """Generate embeddings via Ollama."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": model, "prompt": text},
                )
                resp.raise_for_status()
                data = resp.json()

            return EmbeddingResponse(
                embedding=data.get("embedding", []),
                model=model,
                input_tokens=data.get("prompt_eval_count", 0),
            )
        except Exception as e:
            raise ModelInferenceError(f"Ollama embedding failed: {e}") from e
