"""PHASE GATE: End-to-end Phase 1 integration test.

Validates the complete Galaxy pipeline from user request through
to code generation, including:
- Simple script generation
- Multi-file project generation
- Crash recovery
- Model swap
- Multi-worker parallelism
"""

import pytest
from pathlib import Path

from galaxy.agents.base import BaseAgent
from galaxy.agents.worker import WorkerAgent
from galaxy.agents.registry import AgentRegistry
from galaxy.core.config import GalaxyConfig
from galaxy.core.kernel import GalaxyKernel
from galaxy.core.types import AgentTier, Task, TaskStatus
from galaxy.events import Event
from galaxy.events.bus import EventBus
from galaxy.forge.validator import ContinuousValidator
from galaxy.models.providers import BaseProvider, ChatResponse, ChatMessage
from galaxy.models.router import ModelRouter
from galaxy.orchestrator.escalation import EscalationManager
from galaxy.orchestrator.orchestrator import Orchestrator
from galaxy.orchestrator.task_graph import TaskGraph
from galaxy.tools.builtin.file_write import FileWriteTool
from galaxy.tools.builtin.file_read import FileReadTool
from galaxy.tools.registry import ToolRegistry
from galaxy.vault.checkpoint import Checkpoint


# ─── Mock Provider ───────────────────────────────────────────────────────────

class MockProvider(BaseProvider):
    provider_name = "mock"

    def __init__(self, content: str = "def main():\n    print('hello galaxy')"):
        self._content = content

    async def is_available(self): return True

    async def chat(self, messages, model, **kwargs):
        return ChatResponse(content=self._content, model=model, total_tokens=30)


def make_setup():
    config = GalaxyConfig(models={
        "master": {"provider": "mock", "model": "mock-14b"},
        "domain": {"provider": "mock", "model": "mock-7b"},
        "worker": {"provider": "mock", "model": "mock-7b"},
        "embedding": {"provider": "mock", "model": "mock-embed"},
    })
    router = ModelRouter(config)
    router.registry.register("mock", MockProvider())
    bus = EventBus()
    return config, router, bus


# ─── E2E: Build Simple Python Script ────────────────────────────────────────

class TestBuildSimplePythonScript:
    """E2E: Plan, execute, and validate a simple Python script."""

    @pytest.mark.asyncio
    async def test_build_simple_python_script(self) -> None:
        config, router, bus = make_setup()
        orch = Orchestrator(config, router, bus)

        task = Task(description="Create hello.py", file_path="hello.py", domain="main")
        await orch.plan([task])
        await orch.execute(max_parallel=1)

        assert orch.task_graph.completed_count == 1
        assert orch.progress == 1.0
        assert task.status == TaskStatus.COMPLETED


# ─── E2E: Build REST API (multi-file) ───────────────────────────────────────

class TestBuildRestAPI:
    """E2E: Multi-file project with dependencies."""

    @pytest.mark.asyncio
    async def test_build_rest_api(self) -> None:
        config, router, bus = make_setup()
        orch = Orchestrator(config, router, bus)

        t_models = Task(description="Create data models", file_path="models.py", domain="backend")
        t_db = Task(description="Create DB setup", file_path="database.py", domain="backend")
        t_routes = Task(description="Create API routes", file_path="routes.py", domain="backend")
        t_main = Task(description="Create main app", file_path="main.py", domain="backend")

        await orch.plan(
            [t_models, t_db, t_routes, t_main],
            dependencies={
                t_db.id: [t_models.id],
                t_routes.id: [t_models.id, t_db.id],
                t_main.id: [t_routes.id],
            }
        )

        await orch.execute(max_parallel=2)

        assert orch.task_graph.completed_count == 4
        assert orch.progress == 1.0
        assert t_models.completed_at <= t_db.completed_at
        assert t_models.completed_at <= t_routes.completed_at
        assert t_routes.completed_at <= t_main.completed_at


# ─── E2E: Crash and Recover ─────────────────────────────────────────────────

class TestCrashAndRecover:
    """E2E: Checkpoint → crash → recovery."""

    def test_crash_and_recover(self, tmp_path: Path) -> None:
        graph = TaskGraph()
        t1 = Task(description="Completed task", file_path="done.py")
        t2 = Task(description="Pending task", file_path="todo.py")
        graph.add_task(t1)
        graph.add_task(t2, dependencies=[t1.id])
        graph.mark_completed(t1.id)

        cp = Checkpoint(workspace=str(tmp_path))
        cp.create({"task_graph": graph.to_dict(), "progress": graph.progress}, label="pre_crash")
        cp.create_crash_marker()

        cp2 = Checkpoint(workspace=str(tmp_path))
        assert cp2.has_crash_marker()

        recovered = cp2.recover_from_crash()
        assert recovered is not None

        restored = TaskGraph.from_dict(recovered["task_graph"])
        assert restored.completed_count == 1
        assert restored.pending_count == 1

        ready = restored.get_ready_tasks()
        assert len(ready) == 1


# ─── E2E: Model Swap ────────────────────────────────────────────────────────

class TestPauseSwapModelResume:
    """E2E: Pause, swap model, resume."""

    @pytest.mark.asyncio
    async def test_pause_swap_model_resume(self) -> None:
        config, router, bus = make_setup()

        assert router.get_model_for_tier(AgentTier.WORKER).model == "mock-7b"

        from galaxy.core.config import ModelConfig
        router.swap_model(AgentTier.WORKER, ModelConfig(provider="mock", model="mock-14b"))

        assert router.get_model_for_tier(AgentTier.WORKER).model == "mock-14b"

        worker = WorkerAgent(name="w1", model_router=router, event_bus=bus)
        response = await worker.invoke_llm(user_message="test")
        assert response.model == "mock-14b"


# ─── E2E: Multi-Worker Parallel ─────────────────────────────────────────────

class TestMultiWorkerParallel:
    """E2E: Multiple workers run in parallel."""

    @pytest.mark.asyncio
    async def test_multi_worker_parallel(self) -> None:
        config, router, bus = make_setup()
        orch = Orchestrator(config, router, bus)

        tasks = [Task(description=f"File {i}", file_path=f"file_{i}.py") for i in range(5)]
        await orch.plan(tasks)
        await orch.execute(max_parallel=3)

        assert orch.task_graph.completed_count == 5
        assert orch.progress == 1.0


# ─── E2E: Tool + Validator ──────────────────────────────────────────────────

class TestToolAndValidator:
    """E2E: Write file via tool, then validate it."""

    @pytest.mark.asyncio
    async def test_write_and_validate(self, tmp_path: Path) -> None:
        tool = FileWriteTool(workspace=str(tmp_path))
        result = await tool.execute(path="app.py", content="def main():\n    return 42\n")
        assert result.success

        validator = ContinuousValidator(workspace=str(tmp_path))
        results = await validator.validate_file("app.py")
        assert results[0].passed


# ─── E2E: Full Lifecycle ────────────────────────────────────────────────────

class TestFullLifecycle:
    """E2E: Boot → plan → execute → checkpoint → shutdown."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, tmp_path: Path) -> None:
        config, router, bus = make_setup()

        # Boot
        kernel = GalaxyKernel()
        await kernel.boot(workspace=tmp_path)
        assert kernel.is_booted

        # Orchestrate
        orch = Orchestrator(config, router, bus)
        tasks = [
            Task(description="Create models", file_path="models.py"),
            Task(description="Create views", file_path="views.py"),
        ]
        await orch.plan(tasks)
        await orch.execute(max_parallel=2)
        assert orch.task_graph.completed_count == 2

        # Checkpoint
        cp = Checkpoint(workspace=str(tmp_path))
        cp.create({"graph": orch.task_graph.to_dict()}, label="final")
        assert len(cp.list_checkpoints()) >= 1

        # Shutdown
        await kernel.shutdown()
        assert not kernel.is_booted


# ─── E2E: Event Propagation ─────────────────────────────────────────────────

class TestEventPropagation:
    """E2E: Events flow through the entire system."""

    @pytest.mark.asyncio
    async def test_events_flow_through_system(self) -> None:
        config, router, bus = make_setup()
        all_events: list[Event] = []

        async def capture_all(e: Event):
            all_events.append(e)

        bus.subscribe("*", capture_all)

        orch = Orchestrator(config, router, bus)
        await orch.plan([Task(description="Single task", file_path="t.py")])
        await orch.execute()

        event_types = {e.type for e in all_events}
        assert any("orchestrator" in t for t in event_types)
        assert any("agent" in t for t in event_types)
