"""Base tool interface for Galaxy.

Every tool agents can use must implement this interface.
Tools are registered in the ToolRegistry and exposed to agents via function calling.
"""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from typing import Any

from galaxy.core.types import AgentTier, ToolResult

logger = logging.getLogger(__name__)


@dataclass
class ToolParameter:
    """Definition of a single tool parameter."""

    name: str
    type: str  # "string", "integer", "boolean", "array", "object"
    description: str = ""
    required: bool = True
    default: Any = None
    enum: list[str] | None = None


@dataclass
class ToolDefinition:
    """Complete tool definition for function calling."""

    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)
    allowed_tiers: list[AgentTier] = field(
        default_factory=lambda: [AgentTier.MASTER, AgentTier.DOMAIN, AgentTier.WORKER]
    )
    requires_approval: bool = False
    dangerous: bool = False

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert to OpenAI function calling schema."""
        properties: dict[str, Any] = {}
        required: list[str] = []

        for param in self.parameters:
            prop: dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


class BaseTool(abc.ABC):
    """Abstract base class for all Galaxy tools."""

    @property
    @abc.abstractmethod
    def definition(self) -> ToolDefinition:
        """Return tool definition with name, description, and parameters."""
        ...

    @abc.abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given arguments.

        Returns:
            ToolResult with success/failure and output.
        """
        ...

    def validate_inputs(self, **kwargs: Any) -> str | None:
        """Validate inputs against parameter definitions.

        Returns:
            Error message string if validation fails, None if valid.
        """
        for param in self.definition.parameters:
            if param.required and param.name not in kwargs:
                return f"Missing required parameter: {param.name}"
        return None

    async def safe_execute(self, **kwargs: Any) -> ToolResult:
        """Execute with input validation and error handling."""
        error = self.validate_inputs(**kwargs)
        if error:
            return ToolResult(success=False, error=error)

        try:
            return await self.execute(**kwargs)
        except Exception as e:
            logger.exception("Tool %s failed", self.definition.name)
            return ToolResult(success=False, error=str(e))
