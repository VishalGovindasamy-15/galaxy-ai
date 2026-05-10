"""Model router — routes requests to the right provider based on agent tier and task type.

The router is the single interface agents use to call LLMs. It handles:
- Tier-based routing (master/domain/worker → appropriate model)
- Task-type routing overrides
- Fallback chain when primary model fails
- Model swapping at runtime
"""

from __future__ import annotations

import logging
from typing import Any

from galaxy.core.config import GalaxyConfig, ModelConfig
from galaxy.core.exceptions import ModelInferenceError, ModelNotAvailableError
from galaxy.core.types import AgentTier
from galaxy.models.providers import BaseProvider, ChatMessage, ChatResponse, EmbeddingResponse
from galaxy.models.providers.ollama import OllamaProvider
from galaxy.models.providers.openai_compat import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry of all available LLM providers."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    def register(self, name: str, provider: BaseProvider) -> None:
        self._providers[name] = provider
        logger.debug("Registered provider: %s", name)

    def get(self, name: str) -> BaseProvider | None:
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    async def detect_available(self) -> list[str]:
        """Check which providers are currently available."""
        available: list[str] = []
        for name, provider in self._providers.items():
            try:
                if await provider.is_available():
                    available.append(name)
            except Exception:
                pass
        return available


class ModelRouter:
    """Routes model requests to the appropriate provider based on tier and config.

    Usage:
        router = ModelRouter(config)
        await router.initialize()
        response = await router.chat(tier=AgentTier.WORKER, messages=[...])
    """

    def __init__(self, config: GalaxyConfig) -> None:
        self.config = config
        self.registry = ProviderRegistry()
        self._tier_configs: dict[AgentTier, ModelConfig] = {
            AgentTier.MASTER: config.models.master,
            AgentTier.DOMAIN: config.models.domain,
            AgentTier.WORKER: config.models.worker,
        }
        self._embedding_config = config.models.embedding
        self._consecutive_failures: dict[str, int] = {}

    async def initialize(self) -> None:
        """Initialize and register all configured providers."""
        # Always register Ollama
        ollama = OllamaProvider(
            base_url=self.config.models.master.base_url or "http://localhost:11434"
        )
        self.registry.register("ollama", ollama)

        # Register cloud providers if API keys are configured
        for mc in [self.config.models.master, self.config.models.domain, self.config.models.worker]:
            if mc.provider != "ollama" and mc.provider not in self.registry.list_providers():
                provider = OpenAICompatibleProvider(
                    provider_name=mc.provider,
                    api_key_env=mc.api_key_env,
                    base_url=mc.base_url or f"https://api.{mc.provider}.com/v1",
                )
                self.registry.register(mc.provider, provider)

        # Register fallback if enabled
        if self.config.models.fallback.enabled:
            fb = self.config.models.fallback
            if fb.provider not in self.registry.list_providers():
                fallback = OpenAICompatibleProvider(
                    provider_name=fb.provider,
                    api_key_env=fb.api_key_env,
                    base_url=fb.base_url or f"https://api.{fb.provider}.com/v1",
                )
                self.registry.register(fb.provider, fallback)

        available = await self.registry.detect_available()
        logger.info("Available providers: %s", available)

    async def chat(
        self,
        tier: AgentTier,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        task_type: str | None = None,
    ) -> ChatResponse:
        """Route a chat request to the appropriate model.

        Args:
            tier: Agent tier (master/domain/worker).
            messages: Chat messages.
            tools: Tool definitions.
            task_type: Optional task type for routing overrides.

        Returns:
            ChatResponse from the selected model.

        Raises:
            ModelNotAvailableError: If no model is available.
            ModelInferenceError: If inference fails after fallback.
        """
        model_config = self._tier_configs[tier]
        provider = self.registry.get(model_config.provider)

        if not provider:
            raise ModelNotAvailableError(
                model_config.model, provider=model_config.provider,
                message=f"Provider '{model_config.provider}' not registered",
            )

        try:
            response = await provider.chat(
                messages=messages,
                model=model_config.model,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                tools=tools,
                timeout=model_config.timeout_seconds,
            )
            # Reset failure counter on success
            self._consecutive_failures[model_config.provider] = 0
            return response

        except (ModelNotAvailableError, ModelInferenceError) as e:
            # Track failures for fallback trigger
            key = model_config.provider
            self._consecutive_failures[key] = self._consecutive_failures.get(key, 0) + 1
            logger.warning(
                "Model %s failed (%d consecutive): %s",
                model_config.model,
                self._consecutive_failures[key],
                e,
            )

            # Try fallback if configured and threshold reached
            if (
                self.config.models.fallback.enabled
                and self._consecutive_failures[key] >= self.config.models.fallback.trigger_after_failures
            ):
                return await self._try_fallback(messages, tools)

            raise

    async def embed(self, text: str) -> EmbeddingResponse:
        """Generate embeddings using the configured embedding model."""
        provider = self.registry.get(self._embedding_config.provider)
        if not provider:
            raise ModelNotAvailableError(
                self._embedding_config.model,
                provider=self._embedding_config.provider,
            )
        return await provider.embed(text, self._embedding_config.model)

    def swap_model(self, tier: AgentTier, new_config: ModelConfig) -> None:
        """Swap the model for a specific tier at runtime.

        Args:
            tier: Which tier to update.
            new_config: New model configuration.
        """
        old = self._tier_configs[tier]
        self._tier_configs[tier] = new_config
        logger.info(
            "Swapped %s model: %s/%s → %s/%s",
            tier.value, old.provider, old.model,
            new_config.provider, new_config.model,
        )

    def get_model_for_tier(self, tier: AgentTier) -> ModelConfig:
        """Get current model config for a tier."""
        return self._tier_configs[tier]

    async def _try_fallback(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None,
    ) -> ChatResponse:
        """Attempt inference with the fallback model."""
        fb = self.config.models.fallback
        provider = self.registry.get(fb.provider)
        if not provider:
            raise ModelNotAvailableError(fb.model, provider=fb.provider)

        logger.warning("Falling back to %s/%s", fb.provider, fb.model)
        try:
            return await provider.chat(
                messages=messages,
                model=fb.model,
                tools=tools,
            )
        except Exception as e:
            raise ModelInferenceError(
                f"Fallback model also failed: {e}"
            ) from e
