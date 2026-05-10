"""Worker Agent — the code generator.

Workers are the lowest tier agents that directly write code, tests, and config files.
They receive specific task assignments from Domain agents and execute them.
"""

from __future__ import annotations

import logging
from typing import Any

from galaxy.agents.base import BaseAgent
from galaxy.core.types import AgentStatus, AgentTier, Task, TaskStatus
from galaxy.events.bus import EventBus
from galaxy.models.providers import ChatMessage
from galaxy.models.router import ModelRouter

logger = logging.getLogger(__name__)

WORKER_SYSTEM_PROMPT = """You are a Galaxy Worker Agent — a precise code generator.

Your job is to write production-grade code for a single file.

Rules:
- Write COMPLETE, working code — no placeholders, no TODOs
- Include proper type hints (Python 3.11+)
- Include docstrings for all public functions/classes
- Handle errors gracefully
- Follow the project's coding style
- If writing a test, ensure it's self-contained and uses pytest

Output ONLY the file contents. No explanations, no markdown fences.
"""


class WorkerAgent(BaseAgent):
    """Worker agent that generates individual files."""

    def __init__(
        self,
        name: str,
        model_router: ModelRouter,
        event_bus: EventBus,
        domain: str = "",
        agent_id: str | None = None,
    ) -> None:
        super().__init__(
            name=name,
            tier=AgentTier.WORKER,
            model_router=model_router,
            event_bus=event_bus,
            domain=domain,
            agent_id=agent_id,
        )

    async def execute_task(self, task: Task, context: str = "") -> str:
        """Execute a single task — generate code for a file.

        Args:
            task: The task to execute.
            context: Additional context (project structure, related files, etc.).

        Returns:
            Generated code as a string.
        """
        self.status = AgentStatus.WORKING
        self.current_task = task.description
        task.mark_running(self.id)

        await self.emit_event("agent.task.started", {
            "agent_id": self.id,
            "task_id": task.id,
            "file": task.file_path,
        })

        try:
            prompt = self._build_prompt(task, context)
            response = await self.invoke_llm(
                system_prompt=WORKER_SYSTEM_PROMPT,
                user_message=prompt,
            )

            code = self._extract_code(response.content)

            self.tasks_completed += 1
            self.status = AgentStatus.IDLE
            self.current_task = ""
            task.mark_completed()

            await self.emit_event("agent.task.completed", {
                "agent_id": self.id,
                "task_id": task.id,
                "file": task.file_path,
                "tokens": response.total_tokens,
            })

            return code

        except Exception as e:
            self.tasks_failed += 1
            self.status = AgentStatus.FAILED
            task.mark_failed(str(e))

            await self.emit_event("agent.task.failed", {
                "agent_id": self.id,
                "task_id": task.id,
                "error": str(e),
            })

            raise

    def _build_prompt(self, task: Task, context: str) -> str:
        """Build the prompt for code generation."""
        parts = [f"Generate the file: {task.file_path}"]

        if task.description:
            parts.append(f"\nTask: {task.description}")

        if context:
            parts.append(f"\nProject context:\n{context}")

        if task.metadata:
            if "dependencies" in task.metadata:
                parts.append(f"\nDependencies: {task.metadata['dependencies']}")
            if "style" in task.metadata:
                parts.append(f"\nStyle: {task.metadata['style']}")

        return "\n".join(parts)

    @staticmethod
    def _extract_code(content: str) -> str:
        """Extract code from LLM response, stripping markdown fences if present."""
        content = content.strip()

        # Remove markdown code fences
        if content.startswith("```"):
            lines = content.split("\n")
            # Find opening and closing fence
            start = 1  # Skip first line (```python or ```)
            end = len(lines) - 1
            if lines[-1].strip() == "```":
                end = len(lines) - 1
            content = "\n".join(lines[start:end])

        return content.strip()
