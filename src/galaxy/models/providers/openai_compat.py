"""OpenAI-compatible LLM provider.

Supports OpenAI, and any OpenAI-compatible API (Groq, DeepSeek, vLLM, LiteLLM, custom).
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from galaxy.core.exceptions import ModelInferenceError, ModelNotAvailableError, ModelRateLimitError
from galaxy.models.providers import BaseProvider, ChatMessage, ChatResponse, EmbeddingResponse

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(BaseProvider):
    """OpenAI-compatible provider (works with OpenAI, Groq, DeepSeek, vLLM, LiteLLM)."""

    def __init__(
        self,
        provider_name: str = "openai",
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str = "https://api.openai.com/v1",
        api_key: str | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.api_key_env = api_key_env
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key

    @property
    def api_key(self) -> str | None:
        return self._api_key or os.environ.get(self.api_key_env)

    async def is_available(self) -> bool:
        """Check if API key is set and endpoint is reachable."""
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        tools: list[dict[str, Any]] | None = None,
        timeout: float = 120.0,
    ) -> ChatResponse:
        """Send chat completion to OpenAI-compatible API."""
        if not self.api_key:
            raise ModelNotAvailableError(
                model, provider=self.provider_name,
                message=f"API key not set (env: {self.api_key_env})",
            )

        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

                if resp.status_code == 429:
                    raise ModelRateLimitError(
                        f"Rate limited by {self.provider_name}: {resp.text[:200]}"
                    )

                resp.raise_for_status()
                data = resp.json()

            choice = data["choices"][0]
            message = choice["message"]
            usage = data.get("usage", {})

            return ChatResponse(
                content=message.get("content", "") or "",
                tool_calls=message.get("tool_calls", []),
                model=data.get("model", model),
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                finish_reason=choice.get("finish_reason", ""),
            )

        except (ModelNotAvailableError, ModelRateLimitError):
            raise
        except httpx.ConnectError:
            raise ModelNotAvailableError(
                model, provider=self.provider_name,
                message=f"Cannot connect to {self.base_url}",
            )
        except httpx.TimeoutException:
            raise ModelInferenceError(
                f"{self.provider_name} request timed out after {timeout}s"
            )
        except Exception as e:
            raise ModelInferenceError(
                f"{self.provider_name} inference failed: {e}"
            ) from e

    async def embed(self, text: str, model: str) -> EmbeddingResponse:
        """Generate embeddings via OpenAI-compatible API."""
        if not self.api_key:
            raise ModelNotAvailableError(model, provider=self.provider_name)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"model": model, "input": text},
                )
                resp.raise_for_status()
                data = resp.json()

            return EmbeddingResponse(
                embedding=data["data"][0]["embedding"],
                model=model,
                input_tokens=data.get("usage", {}).get("prompt_tokens", 0),
            )
        except Exception as e:
            raise ModelInferenceError(
                f"{self.provider_name} embedding failed: {e}"
            ) from e


# ─── Pre-configured provider factories ──────────────────────────────────────


def create_openai_provider(api_key: str | None = None) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        provider_name="openai", api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1", api_key=api_key,
    )


def create_groq_provider(api_key: str | None = None) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        provider_name="groq", api_key_env="GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1", api_key=api_key,
    )


def create_deepseek_provider(api_key: str | None = None) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        provider_name="deepseek", api_key_env="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com/v1", api_key=api_key,
    )


def create_vllm_provider(base_url: str = "http://localhost:8000/v1") -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        provider_name="vllm", api_key_env="", base_url=base_url, api_key="dummy",
    )


def create_litellm_provider(base_url: str = "http://localhost:4000/v1") -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        provider_name="litellm", api_key_env="", base_url=base_url, api_key="dummy",
    )


def create_custom_provider(
    base_url: str, api_key: str | None = None,
) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        provider_name="custom", api_key_env="CUSTOM_MODEL_API_KEY",
        base_url=base_url, api_key=api_key,
    )
