"""MODULE GATE: Orchestrator integration test.

Validates the full pipeline: plan → execute → checkpoint → resume.
"""

import pytest

from galaxy.core.config import GalaxyConfig
from galaxy.core.types import Task, TaskStatus
from galaxy.events import Event
from galaxy.events.bus import EventBus
from galaxy.models.providers import BaseProvider, ChatResponse
from galaxy.models.router import ModelRouter
from galaxy.orchestrator.orchestrator import Orchestrator
from galaxy.orchestrator.task_graph import TaskGraph
from galaxy.vault.checkpoint import Checkpoint


class MockProvider(BaseProvider):
    provider_name = "mock"
    async def is_available(self): return True
    async def chat(self, messages, model, **kwargs):
        return ChatResponse(content="def main():\n    pass", model=model, total_tokens=20)


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
    return config, router, bus


class TestFullPipelinePlanToExecute:
    """Test full orchestration pipeline."""

    @pytest.mark.asyncio
    async def test_plan_and_execute(self, setup) -> None:
        config, router, bus = setup
        orch = Orchestrator(config, router, bus)

        # Create tasks
        tasks = [
            Task(description="Create models", file_path="models.py", domain="backend"),
            Task(description="Create routes", file_path="routes.py", domain="backend"),
        ]

        # Plan
        await orch.plan(tasks)
        assert orch.task_graph.total_tasks == 2

        # Execute
        await orch.execute(max_parallel=2)

        assert orch.task_graph.completed_count == 2
        assert orch.progress == 1.0

    @pytest.mark.asyncio
    async def test_plan_with_dependencies(self, setup) -> None:
        config, router, bus = setup
        orch = Orchestrator(config, router, bus)

        t1 = Task(description="DB setup", file_path="db.py")
        t2 = Task(description="Models (needs DB)", file_path="models.py")
        t3 = Task(description="Routes (needs models)", file_path="routes.py")

        await orch.plan(
            [t1, t2, t3],
            dependencies={t2.id: [t1.id], t3.id: [t2.id]},
        )

        await orch.execute(max_parallel=1)
        assert orch.task_graph.completed_count == 3


class TestCheckpointAndResume:
    """Test checkpointing during execution."""

    def test_checkpoint_task_graph(self, tmp_path) -> None:
        graph = TaskGraph()
        t1 = Task(description="A", file_path="a.py")
        t2 = Task(description="B", file_path="b.py")
        graph.add_task(t1)
        graph.add_task(t2, dependencies=[t1.id])
        graph.mark_completed(t1.id)

        # Checkpoint
        cp = Checkpoint(workspace=str(tmp_path))
        state = {"task_graph": graph.to_dict(), "progress": graph.progress}
        cp.create(state, label="mid_execution")

        # Load
        restored_state = cp.load_latest()
        restored_graph = TaskGraph.from_dict(restored_state["task_graph"])

        assert restored_graph.total_tasks == 2
        assert restored_graph.completed_count == 1


class TestOrchestratorEvents:
    """Test that orchestrator emits events."""

    @pytest.mark.asyncio
    async def test_emits_lifecycle_events(self, setup) -> None:
        config, router, bus = setup
        orch = Orchestrator(config, router, bus)
        events: list[Event] = []

        async def capture(e: Event):
            events.append(e)

        bus.subscribe("orchestrator.*", capture)

        await orch.plan([Task(description="T1", file_path="t1.py")])
        await orch.execute()

        event_types = [e.type for e in events]
        assert "orchestrator.planned" in event_types
        assert "orchestrator.started" in event_types
        assert "orchestrator.completed" in event_types
