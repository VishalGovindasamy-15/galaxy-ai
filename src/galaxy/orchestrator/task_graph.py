"""Task graph — DAG-based task dependency manager.

Manages task ordering, dependency resolution, parallel scheduling,
and dynamic task insertion for live plan updates.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from galaxy.core.exceptions import CircularDependencyError, TaskGraphError
from galaxy.core.types import Task, TaskStatus

logger = logging.getLogger(__name__)


class TaskGraph:
    """Directed Acyclic Graph for task dependency management.

    Supports:
    - Adding tasks with dependencies
    - Getting ready-to-execute tasks (all deps satisfied)
    - Critical path analysis
    - Dynamic task insertion (mid-execution updates)
    - Serialization for checkpointing
    """

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._dependencies: dict[str, set[str]] = {}  # task_id → set of dependency task_ids
        self._dependents: dict[str, set[str]] = {}    # task_id → set of dependent task_ids

    def add_task(self, task: Task, dependencies: list[str] | None = None) -> None:
        """Add a task with optional dependencies.

        Args:
            task: The task to add.
            dependencies: List of task IDs this task depends on.

        Raises:
            TaskGraphError: If a dependency doesn't exist.
            CircularDependencyError: If adding creates a cycle.
        """
        deps = set(dependencies or [])

        # Validate deps exist
        for dep_id in deps:
            if dep_id not in self._tasks:
                raise TaskGraphError(f"Dependency '{dep_id}' not found in graph")

        self._tasks[task.id] = task
        self._dependencies[task.id] = deps
        self._dependents.setdefault(task.id, set())

        # Register reverse edges
        for dep_id in deps:
            self._dependents.setdefault(dep_id, set()).add(task.id)

        # Check for cycles
        if self._has_cycle():
            # Roll back
            del self._tasks[task.id]
            del self._dependencies[task.id]
            for dep_id in deps:
                self._dependents[dep_id].discard(task.id)
            raise CircularDependencyError(
                f"Adding task '{task.id}' would create a circular dependency"
            )

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_ready_tasks(self) -> list[Task]:
        """Get all tasks ready for execution (all dependencies completed).

        Returns:
            List of tasks whose dependencies are all completed and that
            are still pending.
        """
        ready = []
        for task_id, task in self._tasks.items():
            if task.status != TaskStatus.PENDING:
                continue
            deps = self._dependencies.get(task_id, set())
            if all(
                self._tasks[d].status == TaskStatus.COMPLETED
                for d in deps
                if d in self._tasks
            ):
                ready.append(task)
        return ready

    def mark_completed(self, task_id: str) -> list[Task]:
        """Mark a task as completed and return newly unblocked tasks.

        Returns:
            List of tasks that became ready after this completion.
        """
        task = self._tasks.get(task_id)
        if not task:
            raise TaskGraphError(f"Task '{task_id}' not found")

        task.mark_completed()

        # Find newly unblocked tasks
        unblocked = []
        for dependent_id in self._dependents.get(task_id, set()):
            dependent = self._tasks[dependent_id]
            if dependent.status == TaskStatus.PENDING:
                deps = self._dependencies[dependent_id]
                if all(
                    self._tasks[d].status == TaskStatus.COMPLETED
                    for d in deps
                ):
                    unblocked.append(dependent)

        return unblocked

    def mark_failed(self, task_id: str, error: str = "") -> None:
        """Mark a task as failed."""
        task = self._tasks.get(task_id)
        if task:
            task.mark_failed(error)

    def get_critical_path(self) -> list[Task]:
        """Calculate the critical path (longest dependency chain).

        Returns:
            List of tasks on the critical path, in execution order.
        """
        if not self._tasks:
            return []

        # Topological sort with distance tracking
        distances: dict[str, int] = {}
        predecessors: dict[str, str | None] = {}

        for task_id in self._topological_order():
            deps = self._dependencies.get(task_id, set())
            if not deps:
                distances[task_id] = 1
                predecessors[task_id] = None
            else:
                max_dist = 0
                max_pred = None
                for dep_id in deps:
                    if distances.get(dep_id, 0) > max_dist:
                        max_dist = distances[dep_id]
                        max_pred = dep_id
                distances[task_id] = max_dist + 1
                predecessors[task_id] = max_pred

        if not distances:
            return []

        # Trace back from the longest path
        end_task = max(distances, key=lambda x: distances[x])
        path = []
        current: str | None = end_task
        while current is not None:
            path.append(self._tasks[current])
            current = predecessors.get(current)

        path.reverse()
        return path

    def insert_task(self, task: Task, after: str | None = None, before: str | None = None) -> None:
        """Dynamically insert a task into the graph (for live updates).

        Args:
            task: New task to insert.
            after: Insert after this task ID (add as dependency).
            before: Insert before this task ID (make this a dependency of that task).
        """
        deps: list[str] = []
        if after and after in self._tasks:
            deps.append(after)

        self.add_task(task, dependencies=deps)

        if before and before in self._tasks:
            self._dependencies[before].add(task.id)
            self._dependents.setdefault(task.id, set()).add(before)

    @property
    def total_tasks(self) -> int:
        return len(self._tasks)

    @property
    def completed_count(self) -> int:
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)

    @property
    def failed_count(self) -> int:
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED)

    @property
    def pending_count(self) -> int:
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)

    @property
    def progress(self) -> float:
        """Completion progress as a fraction (0.0 to 1.0)."""
        if not self._tasks:
            return 0.0
        return self.completed_count / self.total_tasks

    def to_dict(self) -> dict[str, Any]:
        """Serialize the graph for checkpointing."""
        return {
            "tasks": {tid: t.to_dict() for tid, t in self._tasks.items()},
            "dependencies": {tid: list(deps) for tid, deps in self._dependencies.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskGraph:
        """Restore graph from checkpoint data."""
        graph = cls()
        # Restore tasks first
        for tid, task_data in data.get("tasks", {}).items():
            task = Task.from_dict(task_data)
            graph._tasks[task.id] = task
            graph._dependencies[task.id] = set()
            graph._dependents[task.id] = set()

        # Restore dependencies
        for tid, deps in data.get("dependencies", {}).items():
            graph._dependencies[tid] = set(deps)
            for dep_id in deps:
                graph._dependents.setdefault(dep_id, set()).add(tid)

        return graph

    def _topological_order(self) -> list[str]:
        """Return task IDs in topological order (Kahn's algorithm)."""
        in_degree: dict[str, int] = {tid: 0 for tid in self._tasks}
        for tid, deps in self._dependencies.items():
            in_degree[tid] = len(deps)

        queue = deque(tid for tid, d in in_degree.items() if d == 0)
        order: list[str] = []

        while queue:
            current = queue.popleft()
            order.append(current)
            for dependent in self._dependents.get(current, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        return order

    def _has_cycle(self) -> bool:
        """Check if the graph has a cycle."""
        order = self._topological_order()
        return len(order) != len(self._tasks)
