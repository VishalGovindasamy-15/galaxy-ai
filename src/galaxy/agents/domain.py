"""Domain Agent — the project manager.

Domain agents manage a specific area of the project (backend, frontend, etc.).
They decompose domain-level plans into individual worker tasks.
"""

from __future__ import annotations

import logging
from typing import Any

from galaxy.agents.base import BaseAgent
from galaxy.core.types import AgentStatus, AgentTier, Task
from galaxy.events.bus import EventBus
from galaxy.models.providers import ChatMessage
from galaxy.models.router import ModelRouter

logger = logging.getLogger(__name__)

DOMAIN_SYSTEM_PROMPT = """You are a Galaxy Domain Agent — a technical project manager.

Your job is to take a domain-level plan and break it into specific file-level tasks.

For each task, specify:
1. file_path: The exact file path to create
2. description: What the file should contain
3. dependencies: Which other files this depends on

Output a JSON array of tasks. Each task has: file_path, description, dependencies (list of file paths).
"""


class DomainAgent(BaseAgent):
    """Domain agent that manages a project area and coordinates workers."""

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
            tier=AgentTier.DOMAIN,
            model_router=model_router,
            event_bus=event_bus,
            domain=domain,
            agent_id=agent_id,
        )
        self.managed_workers: list[str] = []

    async def plan_domain(self, domain_description: str, context: str = "") -> list[Task]:
        """Break a domain-level plan into file-level tasks.

        Args:
            domain_description: What this domain should build.
            context: Project context from master agent.

        Returns:
            List of Tasks for workers to execute.
        """
        self.status = AgentStatus.WORKING
        self.current_task = f"Planning: {domain_description[:50]}"

        prompt = f"Domain: {self.domain}\n\nPlan: {domain_description}"
        if context:
            prompt += f"\n\nProject context:\n{context}"

        response = await self.invoke_llm(
            system_prompt=DOMAIN_SYSTEM_PROMPT,
            user_message=prompt,
        )

        tasks = self._parse_tasks(response.content)

        self.status = AgentStatus.IDLE
        self.current_task = ""
        self.tasks_completed += 1

        await self.emit_event("domain.planned", {
            "agent_id": self.id,
            "domain": self.domain,
            "task_count": len(tasks),
        })

        return tasks

    def _parse_tasks(self, content: str) -> list[Task]:
        """Parse LLM response into Task objects."""
        import json

        try:
            # Try to extract JSON from response
            content = content.strip()
            if "```" in content:
                lines = content.split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_json = not in_json
                        continue
                    if in_json:
                        json_lines.append(line)
                content = "\n".join(json_lines)

            task_data = json.loads(content)
            tasks = []
            for item in task_data:
                tasks.append(Task(
                    description=item.get("description", ""),
                    file_path=item.get("file_path", ""),
                    domain=self.domain,
                    dependencies=item.get("dependencies", []),
                ))
            return tasks

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to parse domain plan: %s", e)
            # Return a single task with the raw content
            return [Task(
                description=content[:200],
                domain=self.domain,
            )]
