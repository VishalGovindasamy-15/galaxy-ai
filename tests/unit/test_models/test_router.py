"""Tests for galaxy.models.router and providers."""

import pytest
from unittest.mock import AsyncMock, patch

from galaxy.core.config import GalaxyConfig, ModelConfig
from galaxy.core.exceptions import ModelNotAvailableError, ModelInferenceError
from galaxy.core.types import AgentTier
from galaxy.models.providers import BaseProvider, ChatMessage, ChatResponse, EmbeddingResponse
from galaxy.models.providers.ollama import OllamaProvider
from galaxy.models.providers.openai_compat import (
    OpenAICompatibleProvider,
    create_openai_provider,
    create_groq_provider,
    create_deepseek_provider,
)
from galaxy.models.router import ModelRouter, ProviderRegistry


# ─── Mock Provider ───────────────────────────────────────────────────────────

class MockProvider(BaseProvider):
    """A test provider that returns canned responses."""

    provider_name = "mock"

    def __init__(self, available: bool = True, response_content: str = "mock response") -> None:
        self._available = available
        self._response_content = response_content
        self.call_count = 0

    async def is_available(self) -> bool:
        return self._available

    async def chat(self, messages, model, temperature=0.1, max_tokens=4096, tools=None, timeout=120.0):
        self.call_count += 1
        return ChatResponse(
            content=self._response_content,
            model=model,
            input_tokens=10,
            output_tokens=20,
            total_tokens=30,
        )

    async def embed(self, text, model):
        return EmbeddingResponse(embedding=[0.1, 0.2, 0.3], model=model, input_tokens=5)

    async def list_models(self):
        return ["mock-model-7b", "mock-model-14b"]


# ─── ProviderRegistry Tests ─────────────────────────────────────────────────

class TestProviderRegistry:
    """Test provider registry."""

    def test_register_and_get(self) -> None:
        registry = ProviderRegistry()
        mock = MockProvider()
        registry.register("mock", mock)
        assert registry.get("mock") is mock

    def test_get_missing(self) -> None:
        registry = ProviderRegistry()
        assert registry.get("nonexistent") is None

    def test_list_providers(self) -> None:
        registry = ProviderRegistry()
        registry.register("a", MockProvider())
        registry.register("b", MockProvider())
        assert set(registry.list_providers()) == {"a", "b"}

    @pytest.mark.asyncio
    async def test_detect_available(self) -> None:
        registry = ProviderRegistry()
        registry.register("available", MockProvider(available=True))
        registry.register("unavailable", MockProvider(available=False))
        available = await registry.detect_available()
        assert "available" in available
        assert "unavailable" not in available


# ─── ModelRouter Tests ───────────────────────────────────────────────────────

class TestModelRouter:
    """Test model router."""

    @pytest.fixture
    def config(self) -> GalaxyConfig:
        return GalaxyConfig(
            models={
                "master": {"provider": "mock", "model": "mock-14b"},
                "domain": {"provider": "mock", "model": "mock-7b"},
                "worker": {"provider": "mock", "model": "mock-7b"},
                "embedding": {"provider": "mock", "model": "mock-embed"},
            }
        )

    @pytest.fixture
    def router(self, config: GalaxyConfig) -> ModelRouter:
        router = ModelRouter(config)
        mock = MockProvider()
        router.registry.register("mock", mock)
        return router

    @pytest.mark.asyncio
    async def test_route_by_tier(self, router: ModelRouter) -> None:
        response = await router.chat(
            tier=AgentTier.WORKER,
            messages=[ChatMessage(role="user", content="hello")],
        )
        assert response.content == "mock response"
        assert response.total_tokens == 30

    @pytest.mark.asyncio
    async def test_route_master(self, router: ModelRouter) -> None:
        response = await router.chat(
            tier=AgentTier.MASTER,
            messages=[ChatMessage(role="user", content="plan this")],
        )
        assert response.model == "mock-14b"

    @pytest.mark.asyncio
    async def test_route_domain(self, router: ModelRouter) -> None:
        response = await router.chat(
            tier=AgentTier.DOMAIN,
            messages=[ChatMessage(role="user", content="plan domain")],
        )
        assert response.model == "mock-7b"

    @pytest.mark.asyncio
    async def test_missing_provider_raises(self) -> None:
        config = GalaxyConfig(
            models={
                "master": {"provider": "nonexistent", "model": "x"},
                "domain": {"provider": "nonexistent", "model": "x"},
                "worker": {"provider": "nonexistent", "model": "x"},
                "embedding": {"provider": "nonexistent", "model": "x"},
            }
        )
        router = ModelRouter(config)
        with pytest.raises(ModelNotAvailableError):
            await router.chat(
                tier=AgentTier.WORKER,
                messages=[ChatMessage(role="user", content="test")],
            )

    def test_swap_model(self, router: ModelRouter) -> None:
        new_config = ModelConfig(provider="mock", model="mock-32b")
        router.swap_model(AgentTier.MASTER, new_config)
        assert router.get_model_for_tier(AgentTier.MASTER).model == "mock-32b"

    @pytest.mark.asyncio
    async def test_embed(self, router: ModelRouter) -> None:
        response = await router.embed("test text")
        assert len(response.embedding) > 0

    def test_get_model_for_tier(self, router: ModelRouter) -> None:
        config = router.get_model_for_tier(AgentTier.WORKER)
        assert config.model == "mock-7b"


class TestFailoverRouter:
    """Test fallback behavior."""

    @pytest.mark.asyncio
    async def test_fallback_on_failure(self) -> None:
        config = GalaxyConfig(
            models={
                "master": {"provider": "failing", "model": "fail-model"},
                "domain": {"provider": "failing", "model": "fail-model"},
                "worker": {"provider": "failing", "model": "fail-model"},
                "embedding": {"provider": "mock", "model": "mock-embed"},
                "fallback": {
                    "enabled": True,
                    "provider": "backup",
                    "model": "backup-model",
                    "trigger_after_failures": 1,
                },
            }
        )
        router = ModelRouter(config)

        # Register a failing provider
        class FailProvider(BaseProvider):
            provider_name = "failing"
            async def is_available(self): return True
            async def chat(self, messages, model, **kwargs):
                raise ModelInferenceError("always fails")

        router.registry.register("failing", FailProvider())
        router.registry.register("backup", MockProvider(response_content="fallback worked"))

        response = await router.chat(
            tier=AgentTier.WORKER,
            messages=[ChatMessage(role="user", content="test")],
        )
        assert response.content == "fallback worked"


# ─── Provider Factory Tests ─────────────────────────────────────────────────

class TestProviderFactories:
    """Test pre-configured provider factories."""

    def test_openai_factory(self) -> None:
        p = create_openai_provider()
        assert p.provider_name == "openai"
        assert "openai.com" in p.base_url

    def test_groq_factory(self) -> None:
        p = create_groq_provider()
        assert p.provider_name == "groq"
        assert "groq.com" in p.base_url

    def test_deepseek_factory(self) -> None:
        p = create_deepseek_provider()
        assert p.provider_name == "deepseek"


class TestOllamaProvider:
    """Test OllamaProvider construction."""

    def test_default_url(self) -> None:
        p = OllamaProvider()
        assert "11434" in p.base_url

    def test_custom_url(self) -> None:
        p = OllamaProvider(base_url="http://remote:8080")
        assert p.base_url == "http://remote:8080"

    @pytest.mark.asyncio
    async def test_is_available_no_server(self) -> None:
        p = OllamaProvider(base_url="http://localhost:59999")
        assert await p.is_available() is False


class TestOpenAICompatProvider:
    """Test OpenAI-compatible provider."""

    def test_no_api_key(self) -> None:
        p = OpenAICompatibleProvider(api_key_env="NONEXISTENT_TEST_KEY_XYZ")
        assert p.api_key is None

    def test_explicit_api_key(self) -> None:
        p = OpenAICompatibleProvider(api_key="sk-test123")
        assert p.api_key == "sk-test123"

    @pytest.mark.asyncio
    async def test_chat_without_key_raises(self) -> None:
        p = OpenAICompatibleProvider(api_key_env="NONEXISTENT_TEST_KEY_XYZ")
        with pytest.raises(ModelNotAvailableError):
            await p.chat(
                messages=[ChatMessage(role="user", content="test")],
                model="gpt-4o",
            )
