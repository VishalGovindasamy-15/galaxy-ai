"""Orchestrator engine — coordinates the full execution pipeline.

The orchestrator ties together:
- Master agent (planning)
- Domain agents (decomposition)
- Worker agents (execution)
- Task graph (scheduling)
- Escalation (failure handling)
- Checkpoint (persistence)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from galaxy.agents.registry import AgentRegistry
from galaxy.agents.worker import WorkerAgent
from galaxy.core.config import GalaxyConfig
from galaxy.core.types import AgentTier, Task, TaskStatus
from galaxy.events import Event
from galaxy.events.bus import EventBus
from galaxy.models.router import ModelRouter
from galaxy.orchestrator.escalation import EscalationManager
from galaxy.orchestrator.task_graph import TaskGraph

logger = logging.getLogger(__name__)


class Orchestrator:
    """Main orchestration engine — drives the build pipeline.

    Lifecycle:
    1. plan() — Master creates project plan, populates task graph
    2. execute() — Workers execute tasks in dependency order
    3. Failures trigger escalation chain
    4. Checkpoints created at milestones
    """

    def __init__(
        self,
        config: GalaxyConfig,
        model_router: ModelRouter,
        event_bus: EventBus,
    ) -> None:
        self.config = config
        self.model_router = model_router
        self.event_bus = event_bus

        self.task_graph = TaskGraph()
        self.agent_registry = AgentRegistry()
        self.escalation = EscalationManager(event_bus)

        self._is_running = False
        self._is_paused = False

    async def plan(self, tasks: list[Task], dependencies: dict[str, list[str]] | None = None) -> None:
        """Load tasks into the task graph.

        Args:
            tasks: List of tasks to execute.
            dependencies: Optional dict mapping task_id → list of dependency task_ids.
        """
        deps = dependencies or {}

        # Add tasks in dependency order
        added: set[str] = set()

        def _add_with_deps(task: Task) -> None:
            if task.id in added:
                return
            for dep_id in deps.get(task.id, []):
                dep_task = next((t for t in tasks if t.id == dep_id), None)
                if dep_task and dep_task.id not in added:
                    _add_with_deps(dep_task)
            self.task_graph.add_task(task, deps.get(task.id))
            added.add(task.id)

        for task in tasks:
            _add_with_deps(task)

        await self.event_bus.publish(Event(
            type="orchestrator.planned",
            payload={"total_tasks": self.task_graph.total_tasks},
        ))

        logger.info("Orchestrator planned %d tasks", self.task_graph.total_tasks)

    async def execute(self, max_parallel: int = 3) -> None:
        """Execute all tasks in the graph.

        Runs tasks in dependency order with configurable parallelism.

        Args:
            max_parallel: Maximum number of concurrent workers.
        """
        self._is_running = True
        self._is_paused = False

        await self.event_bus.publish(Event(
            type="orchestrator.started",
            payload={"max_parallel": max_parallel},
        ))

        try:
            while self._is_running:
                if self._is_paused:
                    await asyncio.sleep(0.5)
                    continue

                ready_tasks = self.task_graph.get_ready_tasks()

                if not ready_tasks and self.task_graph.pending_count == 0:
                    break  # All done

                if not ready_tasks:
                    # Tasks exist but none ready — wait for running ones
                    await asyncio.sleep(0.1)
                    continue

                # Execute batch
                batch = ready_tasks[:max_parallel]
                await asyncio.gather(
                    *[self._execute_task(task) for task in batch],
                    return_exceptions=True,
                )

        finally:
            self._is_running = False

        await self.event_bus.publish(Event(
            type="orchestrator.completed",
            payload={
                "completed": self.task_graph.completed_count,
                "failed": self.task_graph.failed_count,
                "total": self.task_graph.total_tasks,
            },
        ))

    async def _execute_task(self, task: Task) -> None:
        """Execute a single task with error handling and escalation."""
        worker = WorkerAgent(
            name=f"worker_{task.id[:8]}",
            model_router=self.model_router,
            event_bus=self.event_bus,
            domain=task.domain,
        )
        self.agent_registry.register(worker)

        try:
            await worker.execute_task(task)
            self.task_graph.mark_completed(task.id)
            self.escalation.reset_retries(task.id)

        except Exception as e:
            logger.error("Task %s failed: %s", task.id, e)
            self.task_graph.mark_failed(task.id, str(e))

            try:
                record = await self.escalation.handle_failure(
                    task_id=task.id, error=str(e),
                )
                if record.level == 1:
                    # Reset and retry
                    task.status = TaskStatus.PENDING
                    task.error = ""
            except Exception:
                logger.error("Escalation exhausted for task %s", task.id)

        finally:
            self.agent_registry.unregister(worker.id)

    def pause(self) -> None:
        """Pause execution."""
        self._is_paused = True
        logger.info("Orchestrator paused")

    def resume(self) -> None:
        """Resume execution."""
        self._is_paused = False
        logger.info("Orchestrator resumed")

    def stop(self) -> None:
        """Stop execution entirely."""
        self._is_running = False
        logger.info("Orchestrator stopped")

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    @property
    def progress(self) -> float:
        return self.task_graph.progress
