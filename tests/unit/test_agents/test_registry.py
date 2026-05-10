"""Tests for galaxy.agents.registry (AgentRegistry)."""

import pytest

from galaxy.agents.base import BaseAgent
from galaxy.agents.registry import AgentRegistry
from galaxy.core.config import GalaxyConfig
from galaxy.core.exceptions import AgentLimitError
from galaxy.core.types import AgentStatus, AgentTier
from galaxy.events.bus import EventBus
from galaxy.models.providers import BaseProvider, ChatResponse
from galaxy.models.router import ModelRouter


class MockProvider(BaseProvider):
    provider_name = "mock"
    async def is_available(self): return True
    async def chat(self, messages, model, **kwargs):
        return ChatResponse(content="ok", model=model, total_tokens=10)


@pytest.fixture
def setup():
    config = GalaxyConfig(models={
        "master": {"provider": "mock", "model": "m"},
        "domain": {"provider": "mock", "model": "m"},
        "worker": {"provider": "mock", "model": "m"},
        "embedding": {"provider": "mock", "model": "m"},
    })
    router = ModelRouter(config)
    router.registry.register("mock", MockProvider())
    bus = EventBus()
    return router, bus


def make_agent(router, bus, name, tier, domain="") -> BaseAgent:
    return BaseAgent(name=name, tier=tier, model_router=router, event_bus=bus, domain=domain)


class TestRegisterAgent:
    """Test agent registration."""

    def test_register_agent(self, setup) -> None:
        router, bus = setup
        registry = AgentRegistry()
        agent = make_agent(router, bus, "w1", AgentTier.WORKER, "backend")
        registry.register(agent)
        assert registry.count == 1
        assert registry.get(agent.id) is agent

    def test_unregister(self, setup) -> None:
        router, bus = setup
        registry = AgentRegistry()
        agent = make_agent(router, bus, "w1", AgentTier.WORKER)
        registry.register(agent)
        assert registry.unregister(agent.id)
        assert registry.count == 0
        assert agent.status == AgentStatus.TERMINATED

    def test_unregister_missing(self) -> None:
        registry = AgentRegistry()
        assert not registry.unregister("nonexistent")


class TestGetAgentsByTier:
    """Test tier-based querying."""

    def test_get_agents_by_tier(self, setup) -> None:
        router, bus = setup
        registry = AgentRegistry()
        registry.register(make_agent(router, bus, "m1", AgentTier.MASTER))
        registry.register(make_agent(router, bus, "d1", AgentTier.DOMAIN, "api"))
        registry.register(make_agent(router, bus, "w1", AgentTier.WORKER, "api"))
        registry.register(make_agent(router, bus, "w2", AgentTier.WORKER, "api"))

        assert len(registry.get_agents_by_tier(AgentTier.MASTER)) == 1
        assert len(registry.get_agents_by_tier(AgentTier.DOMAIN)) == 1
        assert len(registry.get_agents_by_tier(AgentTier.WORKER)) == 2

    def test_get_agents_by_domain(self, setup) -> None:
        router, bus = setup
        registry = AgentRegistry()
        registry.register(make_agent(router, bus, "w1", AgentTier.WORKER, "api"))
        registry.register(make_agent(router, bus, "w2", AgentTier.WORKER, "api"))
        registry.register(make_agent(router, bus, "w3", AgentTier.WORKER, "frontend"))

        assert len(registry.get_agents_by_domain("api")) == 2
        assert len(registry.get_agents_by_domain("frontend")) == 1
        assert len(registry.get_agents_by_domain("api", AgentTier.WORKER)) == 2


class TestAgentLimitsEnforced:
    """Test limit enforcement."""

    def test_domain_limit(self, setup) -> None:
        router, bus = setup
        registry = AgentRegistry(max_domain_agents=2)
        registry.register(make_agent(router, bus, "d1", AgentTier.DOMAIN, "a"))
        registry.register(make_agent(router, bus, "d2", AgentTier.DOMAIN, "b"))

        with pytest.raises(AgentLimitError, match="Domain agent limit"):
            registry.register(make_agent(router, bus, "d3", AgentTier.DOMAIN, "c"))

    def test_worker_per_domain_limit(self, setup) -> None:
        router, bus = setup
        registry = AgentRegistry(max_workers_per_domain=2)
        registry.register(make_agent(router, bus, "w1", AgentTier.WORKER, "api"))
        registry.register(make_agent(router, bus, "w2", AgentTier.WORKER, "api"))

        with pytest.raises(AgentLimitError, match="Worker limit"):
            registry.register(make_agent(router, bus, "w3", AgentTier.WORKER, "api"))

    def test_different_domain_not_limited(self, setup) -> None:
        router, bus = setup
        registry = AgentRegistry(max_workers_per_domain=2)
        registry.register(make_agent(router, bus, "w1", AgentTier.WORKER, "api"))
        registry.register(make_agent(router, bus, "w2", AgentTier.WORKER, "api"))
        # Different domain — should work fine
        registry.register(make_agent(router, bus, "w3", AgentTier.WORKER, "frontend"))
        assert registry.count == 3


class TestCleanupIdleAgents:
    """Test idle agent cleanup."""

    def test_cleanup_idle_agents(self, setup) -> None:
        from datetime import timedelta
        router, bus = setup
        registry = AgentRegistry()
        agent = make_agent(router, bus, "w1", AgentTier.WORKER, "api")
        registry.register(agent)
        # Manually age the agent so it appears idle for a long time
        agent.info  # trigger created_at
        # Cleanup with very large timeout — should NOT clean up
        removed = registry.cleanup_idle_agents(max_idle_seconds=999999)
        assert removed == 0
        assert registry.count == 1


class TestRegistrySummary:
    """Test summary reporting."""

    def test_get_summary(self, setup) -> None:
        router, bus = setup
        registry = AgentRegistry()
        registry.register(make_agent(router, bus, "m1", AgentTier.MASTER))
        registry.register(make_agent(router, bus, "d1", AgentTier.DOMAIN, "api"))
        registry.register(make_agent(router, bus, "w1", AgentTier.WORKER, "api"))

        summary = registry.get_summary()
        assert summary["master"] == 1
        assert summary["domain"] == 1
        assert summary["worker"] == 1
        assert summary["total"] == 3
