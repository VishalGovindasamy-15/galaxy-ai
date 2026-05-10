"""Tests for galaxy.agents.worker (WorkerAgent)."""

import pytest

from galaxy.agents.worker import WorkerAgent
from galaxy.core.config import GalaxyConfig
from galaxy.core.types import AgentStatus, Task, TaskStatus
from galaxy.events import Event
from galaxy.events.bus import EventBus
from galaxy.models.providers import BaseProvider, ChatResponse, EmbeddingResponse
from galaxy.models.router import ModelRouter


class MockProvider(BaseProvider):
    provider_name = "mock"
    def __init__(self, content="def hello():\n    return 'world'"):
        self._content = content
    async def is_available(self): return True
    async def chat(self, messages, model, **kwargs):
        return ChatResponse(content=self._content, model=model, total_tokens=50)


@pytest.fixture
def worker_setup():
    config = GalaxyConfig(models={
        "master": {"provider": "mock", "model": "m"},
        "domain": {"provider": "mock", "model": "m"},
        "worker": {"provider": "mock", "model": "m"},
        "embedding": {"provider": "mock", "model": "m"},
    })
    router = ModelRouter(config)
    router.registry.register("mock", MockProvider())
    bus = EventBus()
    worker = WorkerAgent(name="w1", model_router=router, event_bus=bus, domain="backend")
    return worker, bus


class TestWorkerExecutesTask:
    """Test worker task execution."""

    @pytest.mark.asyncio
    async def test_worker_executes_simple_task(self, worker_setup) -> None:
        worker, bus = worker_setup
        task = Task(description="Create hello module", file_path="hello.py")

        code = await worker.execute_task(task)

        assert "def hello" in code
        assert task.status == TaskStatus.COMPLETED
        assert worker.tasks_completed == 1
        assert worker.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_worker_writes_file(self, worker_setup) -> None:
        worker, bus = worker_setup
        task = Task(description="Write utils.py", file_path="src/utils.py")

        code = await worker.execute_task(task)

        assert len(code) > 0
        assert task.completed_at is not None

    @pytest.mark.asyncio
    async def test_worker_emits_events(self, worker_setup) -> None:
        worker, bus = worker_setup
        events: list[Event] = []

        async def capture(e: Event):
            events.append(e)

        bus.subscribe("agent.*", capture)
        task = Task(description="Test", file_path="test.py")
        await worker.execute_task(task)

        event_types = [e.type for e in events]
        assert "agent.task.started" in event_types
        assert "agent.task.completed" in event_types

    @pytest.mark.asyncio
    async def test_worker_handles_failure(self) -> None:
        class FailProvider(BaseProvider):
            provider_name = "fail"
            async def is_available(self): return True
            async def chat(self, messages, model, **kwargs):
                raise RuntimeError("model crashed")

        config = GalaxyConfig(models={
            "master": {"provider": "fail", "model": "x"},
            "domain": {"provider": "fail", "model": "x"},
            "worker": {"provider": "fail", "model": "x"},
            "embedding": {"provider": "fail", "model": "x"},
        })
        router = ModelRouter(config)
        router.registry.register("fail", FailProvider())
        bus = EventBus()
        worker = WorkerAgent(name="w1", model_router=router, event_bus=bus)
        task = Task(description="Will fail", file_path="fail.py")

        with pytest.raises(RuntimeError):
            await worker.execute_task(task)

        assert task.status == TaskStatus.FAILED
        assert worker.tasks_failed == 1


class TestCodeExtraction:
    """Test markdown fence stripping."""

    def test_extract_plain_code(self) -> None:
        code = WorkerAgent._extract_code("def hello():\n    pass")
        assert code == "def hello():\n    pass"

    def test_extract_from_markdown(self) -> None:
        raw = "```python\ndef hello():\n    pass\n```"
        code = WorkerAgent._extract_code(raw)
        assert code == "def hello():\n    pass"

    def test_extract_strips_whitespace(self) -> None:
        code = WorkerAgent._extract_code("  \n  code  \n  ")
        assert code == "code"
