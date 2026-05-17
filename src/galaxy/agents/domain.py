"""Domain Agent — the project manager.

Domain agents manage a specific area of the project (backend, frontend, etc.).
They decompose domain-level plans into individual worker tasks.

Phase 2 upgrade: Can now output ExecutionContracts for chunk-based generation.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from galaxy.agents.base import BaseAgent
from galaxy.contracts.builder import ContractBuilder, build_contract_from_dict
from galaxy.contracts.types import ExecutionContract
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

DOMAIN_CONTRACT_PROMPT = """You are a Galaxy Domain Agent — a precise technical architect.

Your job is to take a domain plan and produce structured ExecutionContracts.

For each function/class to generate, output a JSON object with:
- target_file: path to the file
- function_name: name of the function or class
- operation: one of create_function, create_class, create_method, modify_function, create_file, add_import, append_code, add_decorator, modify_class, add_constant
- description: what this code should do
- parameters: list of {name, type, description}
- return_spec: {type_hint, description}
- dependencies: list of import names
- constraints: dict of key-value constraints
- validation: list of expected behaviors

Output a JSON array of contracts. NO explanations. ONLY JSON.
"""


class DomainAgent(BaseAgent):
    """Domain agent that manages a project area and coordinates workers.

    Supports two modes:
    - Legacy: plan_domain() → returns Task objects
    - Contract: plan_contracts() → returns ExecutionContract objects
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

    async def plan_contracts(
        self,
        domain_description: str,
        context: str = "",
    ) -> list[ExecutionContract]:
        """Break a domain-level plan into ExecutionContracts.

        This is the Phase 2 contract-based approach that produces
        structured, validated contracts for chunk-based workers.

        Args:
            domain_description: What this domain should build.
            context: Project context from master agent.

        Returns:
            List of ExecutionContracts for workers.
        """
        self.status = AgentStatus.WORKING
        self.current_task = f"Contract planning: {domain_description[:50]}"

        prompt = f"Domain: {self.domain}\n\nPlan: {domain_description}"
        if context:
            prompt += f"\n\nProject context:\n{context}"

        response = await self.invoke_llm(
            system_prompt=DOMAIN_CONTRACT_PROMPT,
            user_message=prompt,
        )

        contracts = self._parse_contracts(response.content)

        self.status = AgentStatus.IDLE
        self.current_task = ""
        self.tasks_completed += 1

        await self.emit_event("domain.contracts.planned", {
            "agent_id": self.id,
            "domain": self.domain,
            "contract_count": len(contracts),
        })

        return contracts

    def build_contract(self) -> ContractBuilder:
        """Get a ContractBuilder pre-configured for this domain."""
        return ContractBuilder(self.domain)

    def _parse_contracts(self, content: str) -> list[ExecutionContract]:
        """Parse LLM response into ExecutionContract objects."""
        try:
            content = self._strip_markdown(content)
            data = json.loads(content)

            if isinstance(data, list):
                contracts = []
                for item in data:
                    item["domain"] = self.domain
                    contracts.append(build_contract_from_dict(item))
                return contracts

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to parse contracts: %s", e)

        # Fallback: single generic contract
        return [
            ContractBuilder(self.domain)
            .target("main.py", "main")
            .description(content[:200])
            .build(validate=False)
        ]

    def _parse_tasks(self, content: str) -> list[Task]:
        """Parse LLM response into Task objects."""
        try:
            content = self._strip_markdown(content)
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

    @staticmethod
    def _strip_markdown(content: str) -> str:
        """Strip markdown code fences from content."""
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
        return content

