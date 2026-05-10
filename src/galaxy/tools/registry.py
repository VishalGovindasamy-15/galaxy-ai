"""Tool registry — manages available tools and generates schemas.

The registry is the single source of truth for what tools agents can use.
It handles tier-based access control and schema generation for function calling.
"""

from __future__ import annotations

import logging
from typing import Any

from galaxy.core.exceptions import ToolNotFoundError, ToolPermissionError
from galaxy.core.types import AgentTier, ToolResult
from galaxy.tools.base import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for all available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        name = tool.definition.name
        self._tools[name] = tool
        logger.debug("Registered tool: %s", name)

    def get(self, name: str) -> BaseTool:
        """Get a tool by name.

        Raises:
            ToolNotFoundError: If tool doesn't exist.
        """
        tool = self._tools.get(name)
        if not tool:
            raise ToolNotFoundError(f"Tool not found: {name}")
        return tool

    def list_tools(self, tier: AgentTier | None = None) -> list[str]:
        """List available tool names, optionally filtered by tier."""
        if tier is None:
            return list(self._tools.keys())
        return [
            name
            for name, tool in self._tools.items()
            if tier in tool.definition.allowed_tiers
        ]

    def get_tools_for_tier(self, tier: AgentTier) -> list[BaseTool]:
        """Get all tools available to a specific agent tier."""
        return [
            tool
            for tool in self._tools.values()
            if tier in tool.definition.allowed_tiers
        ]

    def generate_openai_schemas(self, tier: AgentTier) -> list[dict[str, Any]]:
        """Generate OpenAI function calling schemas for a tier.

        Args:
            tier: Agent tier to generate schemas for.

        Returns:
            List of OpenAI tool schemas.
        """
        tools = self.get_tools_for_tier(tier)
        return [tool.definition.to_openai_schema() for tool in tools]

    async def execute(
        self, name: str, tier: AgentTier, **kwargs: Any,
    ) -> ToolResult:
        """Execute a tool with tier-based permission checking.

        Args:
            name: Tool name.
            tier: Agent tier requesting execution.
            **kwargs: Tool arguments.

        Returns:
            ToolResult.

        Raises:
            ToolNotFoundError: If tool doesn't exist.
            ToolPermissionError: If tier doesn't have access.
        """
        tool = self.get(name)

        if tier not in tool.definition.allowed_tiers:
            raise ToolPermissionError(
                f"Agent tier '{tier.value}' cannot use tool '{name}'"
            )

        return await tool.safe_execute(**kwargs)

    @property
    def count(self) -> int:
        return len(self._tools)
