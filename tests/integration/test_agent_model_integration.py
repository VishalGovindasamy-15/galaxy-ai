"""MODULE GATE: Agent + Model integration test.

Validates that agents call models via the router, workers generate code,
and the agent lifecycle works end-to-end.
"""

import pytest

from galaxy.agents.base import BaseAgent
from galaxy.agents.worker import WorkerAgent
from galaxy.agents.domain import DomainAgent
from galaxy.agents.master import MasterAgent
from galaxy.agents.registry import AgentRegistry
from galaxy.core.config import GalaxyConfig
from galaxy.core.types import AgentTier, Task, TaskStatus
from galaxy.events import Event
from galaxy.events.bus import EventBus
from galaxy.models.providers import BaseProvider, ChatResponse
from galaxy.models.router import ModelRouter


class MockProvider(BaseProvider):
    provider_name = "mock"
    def __init__(self, content="def main():\n    print('hello')"):
        self._content = content
    async def is_available(self): return True
    async def chat(self, messages, model, **kwargs):
        return ChatResponse(content=self._content, model=model, total_tokens=50)


@pytest.fixture
def full_setup():
    config = GalaxyConfig(models={
        "master": {"provider": "mock", "model": "mock-14b"},
        "domain": {"provider": "mock", "model": "mock-7b"},
        "worker": {"provider": "mock", "model": "mock-7b"},
        "embedding": {"provider": "mock", "model": "mock-embed"},
    })
    router = ModelRouter(config)
    router.registry.register("mock", MockProvider())
    bus = EventBus()
    return router, bus


class TestAgentCallsModelViaRouter:
    """Test that agents properly call models through the router."""

    @pytest.mark.asyncio
    async def test_agent_calls_model_via_router(self, full_setup) -> None:
        router, bus = full_setup
        agent = BaseAgent(
            name="test_agent",
            tier=AgentTier.WORKER,
            model_router=router,
            event_bus=bus,
        )

        response = await agent.invoke_llm(user_message="Write a function")

        assert response.content  # Got content back
        assert response.model == "mock-7b"  # Used worker model
        assert agent.total_tokens == 50  # Tracked tokens


class TestWorkerGeneratesCode:
    """Test worker generates code with the mock Ollama-style provider."""

    @pytest.mark.asyncio
    async def test_worker_generates_code(self, full_setup) -> None:
        router, bus = full_setup
        worker = WorkerAgent(
            name="code_worker",
            model_router=router,
            event_bus=bus,
            domain="backend",
        )

        task = Task(
            description="Create a hello world module",
            file_path="src/hello.py",
            domain="backend",
        )

        code = await worker.execute_task(task)

        assert "def main" in code
        assert task.status == TaskStatus.COMPLETED
        assert worker.tasks_completed == 1


class TestAgentLifecycle:
    """Test full agent lifecycle: spawn → work → complete → terminate."""

    @pytest.mark.asyncio
    async def test_agent_lifecycle_spawn_to_terminate(self, full_setup) -> None:
        router, bus = full_setup
        registry = AgentRegistry()

        lifecycle_events: list[str] = []

        async def track_events(event: Event) -> None:
            lifecycle_events.append(event.type)

        bus.subscribe("agent.*", track_events)

        # 1. Spawn worker
        worker = WorkerAgent(
            name="lifecycle_worker",
            model_router=router,
            event_bus=bus,
            domain="api",
        )
        registry.register(worker)
        assert registry.count == 1

        # 2. Execute task
        task = Task(description="Create file", file_path="test.py")
        await worker.execute_task(task)

        # 3. Verify lifecycle
        assert "agent.task.started" in lifecycle_events
        assert "agent.task.completed" in lifecycle_events
        assert task.status == TaskStatus.COMPLETED

        # 4. Terminate
        registry.unregister(worker.id)
        assert registry.count == 0

    @pytest.mark.asyncio
    async def test_multi_agent_workflow(self, full_setup) -> None:
        """Multiple workers execute tasks concurrently through the registry."""
        router, bus = full_setup
        registry = AgentRegistry()

        workers = []
        for i in range(3):
            w = WorkerAgent(name=f"w{i}", model_router=router, event_bus=bus, domain="api")
            registry.register(w)
            workers.append(w)

        assert registry.count == 3

        # Each worker executes a task
        tasks = [Task(description=f"Task {i}", file_path=f"file{i}.py") for i in range(3)]
        for worker, task in zip(workers, tasks):
            await worker.execute_task(task)

        # All completed
        assert all(t.status == TaskStatus.COMPLETED for t in tasks)
        assert sum(w.tasks_completed for w in workers) == 3


class TestAgentCheckpointIntegration:
    """Test checkpoint/restore with live router and bus."""

    @pytest.mark.asyncio
    async def test_checkpoint_restore_and_continue(self, full_setup) -> None:
        router, bus = full_setup

        # Create agent, do work
        worker = WorkerAgent(name="checkpoint_worker", model_router=router, event_bus=bus)
        task = Task(description="First task", file_path="first.py")
        await worker.execute_task(task)

        # Checkpoint
        checkpoint = worker.to_checkpoint()
        assert checkpoint.tasks_completed == 1

        # Restore
        restored = BaseAgent.from_checkpoint(checkpoint, router, bus)
        assert restored.id == worker.id
        assert restored.tasks_completed == 1
        assert len(restored.conversation_history) > 0
