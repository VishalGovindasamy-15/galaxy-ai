"""Worker Agent — the code generator.

Workers are the lowest tier agents that directly write code, tests, and config files.
They receive specific task assignments from Domain agents and execute them.

Phase 2 upgrade: Can now generate CodeChunks from ExecutionContracts.
"""

from __future__ import annotations

import logging
from typing import Any

from galaxy.agents.base import BaseAgent
from galaxy.contracts.types import CodeChunk, ExecutionContract
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

CRITICAL OUTPUT RULES:
- Output ONLY the raw file contents
- Do NOT wrap code in ```python or ``` markdown fences
- Do NOT add any explanations, comments about what the code does, or notes before/after
- Start your response with the first line of code (e.g., import statement or docstring)
- End your response with the last line of code
"""


class WorkerAgent(BaseAgent):
    """Worker agent that generates individual files.

    Supports two modes:
    - Legacy: execute_task() → generates full files from Tasks
    - Contract: execute_contract() → generates CodeChunks from ExecutionContracts
    """

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

    async def execute_contract(
        self,
        contract: ExecutionContract,
        context: str = "",
    ) -> CodeChunk:
        """Execute an ExecutionContract — generate a CodeChunk.

        This is the Phase 2 contract-based approach. The worker
        uses the contract's structured prompt to generate code,
        then wraps it in a CodeChunk for the integrator.

        Args:
            contract: The execution contract specifying what to generate.
            context: Additional project context.

        Returns:
            CodeChunk ready for the integrator.
        """
        self.status = AgentStatus.WORKING
        self.current_task = f"Contract: {contract.function_name}"

        await self.emit_event("worker.contract.started", {
            "agent_id": self.id,
            "contract_id": contract.id,
            "target": f"{contract.target_file}::{contract.function_name}",
        })

        try:
            # Use the contract's structured prompt
            prompt = contract.to_worker_prompt()
            if context:
                prompt += f"\n\nProject context:\n{context}"

            response = await self.invoke_llm(
                system_prompt=WORKER_SYSTEM_PROMPT,
                user_message=prompt,
            )

            code = self._extract_code(response.content)

            chunk = CodeChunk(
                contract_id=contract.id,
                target_file=contract.target_file,
                target_symbol=contract.function_name,
                operation=contract.operation,
                content=code,
                dependencies=contract.dependencies,
                worker_id=self.id,
            )

            self.tasks_completed += 1
            self.status = AgentStatus.IDLE
            self.current_task = ""

            await self.emit_event("worker.contract.completed", {
                "agent_id": self.id,
                "contract_id": contract.id,
                "chunk_lines": len(code.splitlines()),
                "tokens": response.total_tokens,
            })

            return chunk

        except Exception as e:
            self.tasks_failed += 1
            self.status = AgentStatus.FAILED

            await self.emit_event("worker.contract.failed", {
                "agent_id": self.id,
                "contract_id": contract.id,
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
        """Extract code from LLM response, stripping markdown fences and explanations.

        Handles common LLM output patterns:
        - ```python\\ncode\\n```
        - code with trailing ```
        - Multiple code blocks (takes the largest)
        - Explanatory text before/after code blocks
        """
        content = content.strip()

        # Strategy 1: Extract from markdown code blocks (```...```)
        if "```" in content:
            import re
            # Find all code blocks
            blocks = re.findall(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)
            if blocks:
                # Return the largest code block (most likely the actual code)
                return max(blocks, key=len).strip()

            # Fallback: just strip all ``` lines
            lines = content.split("\n")
            clean_lines = [
                line for line in lines
                if not line.strip().startswith("```")
            ]
            return "\n".join(clean_lines).strip()

        return content.strip()


