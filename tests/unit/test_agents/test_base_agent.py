"""Tests for galaxy.agents.base (BaseAgent)."""

import pytest

from galaxy.agents.base import BaseAgent, AgentCheckpoint
from galaxy.core.config import GalaxyConfig, ModelConfig
from galaxy.core.types import AgentStatus, AgentTier
from galaxy.events import Event
from galaxy.events.bus import EventBus
from galaxy.models.providers import ChatMessage, ChatResponse, BaseProvider, EmbeddingResponse
from galaxy.models.router import ModelRouter


# ─── Mock Provider ───────────────────────────────────────────────────────────

class MockProvider(BaseProvider):
    provider_name = "mock"
    async def is_available(self): return True
    async def chat(self, messages, model, **kwargs):
        return ChatResponse(
            content="generated code here",
            model=model, input_tokens=10, output_tokens=20, total_tokens=30,
        )
    async def embed(self, text, model):
        return EmbeddingResponse(embedding=[0.1], model=model)


@pytest.fixture
def mock_router() -> ModelRouter:
    config = GalaxyConfig(
        models={
            "master": {"provider": "mock", "model": "mock-14b"},
            "domain": {"provider": "mock", "model": "mock-7b"},
            "worker": {"provider": "mock", "model": "mock-7b"},
            "embedding": {"provider": "mock", "model": "mock-embed"},
        }
    )
    router = ModelRouter(config)
    router.registry.register("mock", MockProvider())
    return router


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


class TestAgentCreation:
    """Test BaseAgent creation."""

    def test_agent_creation(self, mock_router, event_bus) -> None:
        agent = BaseAgent(
            name="worker_01",
            tier=AgentTier.WORKER,
            model_router=mock_router,
            event_bus=event_bus,
            domain="backend",
        )
        assert agent.name == "worker_01"
        assert agent.tier == AgentTier.WORKER
        assert agent.domain == "backend"
        assert agent.status == AgentStatus.IDLE
        assert agent.id  # auto-generated

    def test_unique_ids(self, mock_router, event_bus) -> None:
        a1 = BaseAgent(name="a", tier=AgentTier.WORKER, model_router=mock_router, event_bus=event_bus)
        a2 = BaseAgent(name="b", tier=AgentTier.WORKER, model_router=mock_router, event_bus=event_bus)
        assert a1.id != a2.id

    def test_info_snapshot(self, mock_router, event_bus) -> None:
        agent = BaseAgent(name="w1", tier=AgentTier.WORKER, model_router=mock_router, event_bus=event_bus)
        info = agent.info
        assert info.name == "w1"
        assert info.tier == AgentTier.WORKER
        assert info.status == AgentStatus.IDLE

    def test_repr(self, mock_router, event_bus) -> None:
        agent = BaseAgent(name="w1", tier=AgentTier.WORKER, model_router=mock_router, event_bus=event_bus)
        r = repr(agent)
        assert "BaseAgent" in r
        assert "w1" in r


class TestInvokeLLM:
    """Test LLM invocation through the router."""

    @pytest.mark.asyncio
    async def test_invoke_llm(self, mock_router, event_bus) -> None:
        agent = BaseAgent(name="w1", tier=AgentTier.WORKER, model_router=mock_router, event_bus=event_bus)
        response = await agent.invoke_llm(user_message="Write hello.py")
        assert response.content == "generated code here"
        assert response.total_tokens == 30

    @pytest.mark.asyncio
    async def test_invoke_tracks_tokens(self, mock_router, event_bus) -> None:
        agent = BaseAgent(name="w1", tier=AgentTier.WORKER, model_router=mock_router, event_bus=event_bus)
        await agent.invoke_llm(user_message="task 1")
        await agent.invoke_llm(user_message="task 2")
        assert agent.total_tokens == 60

    @pytest.mark.asyncio
    async def test_invoke_stores_conversation(self, mock_router, event_bus) -> None:
        agent = BaseAgent(name="w1", tier=AgentTier.WORKER, model_router=mock_router, event_bus=event_bus)
        await agent.invoke_llm(user_message="hello")
        assert len(agent.conversation_history) == 2  # user + assistant
        assert agent.conversation_history[0].role == "user"
        assert agent.conversation_history[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_invoke_with_system_prompt(self, mock_router, event_bus) -> None:
        agent = BaseAgent(name="w1", tier=AgentTier.WORKER, model_router=mock_router, event_bus=event_bus)
        response = await agent.invoke_llm(
            system_prompt="You are a coder",
            user_message="Write code",
        )
        assert response.content == "generated code here"

    @pytest.mark.asyncio
    async def test_invoke_with_explicit_messages(self, mock_router, event_bus) -> None:
        agent = BaseAgent(name="w1", tier=AgentTier.WORKER, model_router=mock_router, event_bus=event_bus)
        response = await agent.invoke_llm(
            messages=[ChatMessage(role="user", content="explicit message")]
        )
        assert response.content == "generated code here"


class TestUseTool:
    """Test event emission (tool use comes in later phases)."""

    @pytest.mark.asyncio
    async def test_emit_event(self, mock_router, event_bus) -> None:
        agent = BaseAgent(name="w1", tier=AgentTier.WORKER, model_router=mock_router, event_bus=event_bus)
        received: list[Event] = []

        async def handler(event: Event) -> None:
            received.append(event)

        event_bus.subscribe("test.event", handler)
        await agent.emit_event("test.event", {"key": "value"})

        assert len(received) == 1
        assert received[0].source == agent.id
        assert received[0].payload["key"] == "value"


class TestCheckpointSerialization:
    """Test checkpoint save/restore."""

    @pytest.mark.asyncio
    async def test_checkpoint_serialization(self, mock_router, event_bus) -> None:
        agent = BaseAgent(
            name="w1", tier=AgentTier.WORKER,
            model_router=mock_router, event_bus=event_bus,
            domain="backend",
        )
        await agent.invoke_llm(user_message="test task")
        agent.tasks_completed = 5

        checkpoint = agent.to_checkpoint()
        assert checkpoint.name == "w1"
        assert checkpoint.tier == "worker"
        assert checkpoint.tasks_completed == 5
        assert len(checkpoint.conversation_history) > 0

    @pytest.mark.asyncio
    async def test_from_checkpoint_restoration(self, mock_router, event_bus) -> None:
        # Create and checkpoint
        agent = BaseAgent(
            name="original", tier=AgentTier.WORKER,
            model_router=mock_router, event_bus=event_bus,
            domain="api",
        )
        await agent.invoke_llm(user_message="task 1")
        agent.tasks_completed = 3
        agent.tasks_failed = 1
        checkpoint = agent.to_checkpoint()

        # Restore
        restored = BaseAgent.from_checkpoint(checkpoint, mock_router, event_bus)
        assert restored.id == agent.id
        assert restored.name == "original"
        assert restored.domain == "api"
        assert restored.tasks_completed == 3
        assert restored.tasks_failed == 1
        assert len(restored.conversation_history) == len(agent.conversation_history)

    def test_reset_conversation(self, mock_router, event_bus) -> None:
        agent = BaseAgent(name="w1", tier=AgentTier.WORKER, model_router=mock_router, event_bus=event_bus)
        agent.conversation_history.append(ChatMessage(role="user", content="test"))
        assert len(agent.conversation_history) == 1
        agent.reset_conversation()
        assert len(agent.conversation_history) == 0
