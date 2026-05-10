"""Tests for galaxy.tools.base and galaxy.tools.registry."""

import pytest

from galaxy.core.exceptions import ToolNotFoundError, ToolPermissionError
from galaxy.core.types import AgentTier, ToolResult
from galaxy.tools.base import BaseTool, ToolDefinition, ToolParameter
from galaxy.tools.registry import ToolRegistry


# ─── Mock Tool ───────────────────────────────────────────────────────────────

class MockTool(BaseTool):
    def __init__(self, name: str = "mock_tool", tiers=None):
        self._name = name
        self._tiers = tiers or [AgentTier.MASTER, AgentTier.DOMAIN, AgentTier.WORKER]

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self._name,
            description="A mock tool for testing",
            parameters=[
                ToolParameter(name="input", type="string", description="Test input"),
                ToolParameter(name="optional", type="string", description="Optional param", required=False),
            ],
            allowed_tiers=self._tiers,
        )

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, output=f"mock: {kwargs.get('input', '')}")


class MasterOnlyTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="master_only",
            description="Only master can use this",
            allowed_tiers=[AgentTier.MASTER],
        )

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, output="master action")


class TestToolDefinition:
    """Test ToolDefinition and OpenAI schema generation."""

    def test_to_openai_schema(self) -> None:
        tool = MockTool()
        schema = tool.definition.to_openai_schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "mock_tool"
        assert "input" in schema["function"]["parameters"]["properties"]
        assert "input" in schema["function"]["parameters"]["required"]
        assert "optional" not in schema["function"]["parameters"]["required"]


class TestToolInputValidation:
    """Test input validation on BaseTool."""

    @pytest.mark.asyncio
    async def test_valid_input(self) -> None:
        tool = MockTool()
        result = await tool.safe_execute(input="hello")
        assert result.success
        assert "hello" in result.output

    @pytest.mark.asyncio
    async def test_missing_required(self) -> None:
        tool = MockTool()
        result = await tool.safe_execute()  # Missing 'input'
        assert not result.success
        assert "Missing required" in result.error

    @pytest.mark.asyncio
    async def test_tool_result_structure(self) -> None:
        tool = MockTool()
        result = await tool.safe_execute(input="test")
        assert isinstance(result, ToolResult)
        assert isinstance(result.success, bool)


class TestToolRegistry:
    """Test tool registry."""

    def test_register_tool(self) -> None:
        registry = ToolRegistry()
        registry.register(MockTool())
        assert registry.count == 1

    def test_get_tool(self) -> None:
        registry = ToolRegistry()
        registry.register(MockTool())
        tool = registry.get("mock_tool")
        assert tool.definition.name == "mock_tool"

    def test_get_nonexistent_raises(self) -> None:
        registry = ToolRegistry()
        with pytest.raises(ToolNotFoundError):
            registry.get("nonexistent")

    def test_list_tools(self) -> None:
        registry = ToolRegistry()
        registry.register(MockTool("tool_a"))
        registry.register(MockTool("tool_b"))
        assert set(registry.list_tools()) == {"tool_a", "tool_b"}

    def test_get_tools_for_tier(self) -> None:
        registry = ToolRegistry()
        registry.register(MockTool("all_tiers"))
        registry.register(MasterOnlyTool())

        worker_tools = registry.get_tools_for_tier(AgentTier.WORKER)
        master_tools = registry.get_tools_for_tier(AgentTier.MASTER)

        assert len(worker_tools) == 1  # Only all_tiers
        assert len(master_tools) == 2  # all_tiers + master_only

    def test_generate_openai_schemas(self) -> None:
        registry = ToolRegistry()
        registry.register(MockTool())
        schemas = registry.generate_openai_schemas(AgentTier.WORKER)
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "mock_tool"

    @pytest.mark.asyncio
    async def test_execute_with_permission(self) -> None:
        registry = ToolRegistry()
        registry.register(MockTool())
        result = await registry.execute("mock_tool", AgentTier.WORKER, input="test")
        assert result.success

    @pytest.mark.asyncio
    async def test_execute_permission_denied(self) -> None:
        registry = ToolRegistry()
        registry.register(MasterOnlyTool())
        with pytest.raises(ToolPermissionError):
            await registry.execute("master_only", AgentTier.WORKER)
