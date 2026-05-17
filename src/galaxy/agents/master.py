"""Master Agent — the architect.

The Master agent receives a project request, decomposes it into domains,
creates the overall project plan, and coordinates domain agents.

Phase 2 upgrade: Uses the CognitivePipeline for deep reasoning before planning.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from galaxy.agents.base import BaseAgent
from galaxy.cognitive.pipeline import CognitivePipeline
from galaxy.cognitive.types import CognitiveMode, PipelineState
from galaxy.core.types import AgentStatus, AgentTier
from galaxy.events.bus import EventBus
from galaxy.models.providers import ChatMessage
from galaxy.models.router import ModelRouter

logger = logging.getLogger(__name__)

MASTER_SYSTEM_PROMPT = """You are the Galaxy Master Agent — a senior software architect.

Your job is to take a high-level project request and create a structured plan:

1. Analyze the request and identify required domains (backend, frontend, database, devops, etc.)
2. For each domain, write a clear description of what needs to be built
3. Identify cross-domain dependencies

Output a JSON object with:
{
  "project_name": "string",
  "description": "string", 
  "domains": [
    {
      "name": "string",
      "description": "string",
      "dependencies": ["domain_name"]
    }
  ]
}
"""


class MasterAgent(BaseAgent):
    """Master agent — the project architect.

    Supports two planning modes:
    - Legacy: plan_project() → direct LLM planning
    - Cognitive: plan_with_cognition() → 5-stage pipeline + LLM planning
    """

    def __init__(
        self,
        name: str = "master",
        model_router: ModelRouter | None = None,
        event_bus: EventBus | None = None,
        agent_id: str | None = None,
        workspace: Path | None = None,
    ) -> None:
        # Allow None for testing — will be set before use
        super().__init__(
            name=name,
            tier=AgentTier.MASTER,
            model_router=model_router,  # type: ignore[arg-type]
            event_bus=event_bus or EventBus(),
            agent_id=agent_id,
        )
        self._workspace = workspace
        self._pipeline = CognitivePipeline(workspace=workspace)
        self._last_pipeline_state: PipelineState | None = None

    @property
    def pipeline(self) -> CognitivePipeline:
        """Access the cognitive pipeline."""
        return self._pipeline

    @property
    def last_pipeline_state(self) -> PipelineState | None:
        """Get the last pipeline execution state."""
        return self._last_pipeline_state

    async def plan_project(self, request: str) -> dict[str, Any]:
        """Create a project plan from a user request.

        Args:
            request: High-level project description (e.g., "Build a REST API with auth").

        Returns:
            Project plan dict with domains and dependencies.
        """
        self.status = AgentStatus.WORKING
        self.current_task = f"Planning: {request[:50]}"

        response = await self.invoke_llm(
            system_prompt=MASTER_SYSTEM_PROMPT,
            user_message=request,
        )

        plan = self._parse_plan(response.content)

        self.status = AgentStatus.IDLE
        self.current_task = ""
        self.tasks_completed += 1

        await self.emit_event("master.planned", {
            "agent_id": self.id,
            "project": plan.get("project_name", ""),
            "domains": len(plan.get("domains", [])),
        })

        return plan

    def plan_with_cognition(
        self,
        request: str,
        mode: CognitiveMode = CognitiveMode.REASONING,
        context: str = "",
    ) -> PipelineState:
        """Plan using the full cognitive pipeline.

        Runs: Expand → Plan → Retrieve → Reflect → Synthesize
        before generating the project plan.

        Args:
            request: High-level project description.
            mode: NORMAL (fast) or REASONING (deep).
            context: Additional context (e.g., from brainstorm).

        Returns:
            PipelineState with all stage results and final plan.
        """
        self.status = AgentStatus.WORKING
        self.current_task = f"Cognitive planning: {request[:50]}"

        state = self._pipeline.run(request, mode=mode, context=context)
        self._last_pipeline_state = state

        self.status = AgentStatus.IDLE
        self.current_task = ""
        self.tasks_completed += 1

        return state

    def _parse_plan(self, content: str) -> dict[str, Any]:
        """Parse LLM response into a project plan."""
        try:
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

            return json.loads(content)

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to parse master plan: %s", e)
            return {
                "project_name": "unknown",
                "description": content[:200],
                "domains": [],
            }

