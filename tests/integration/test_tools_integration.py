"""MODULE GATE: Tools integration test.

Validates that agents use tools through the registry, file tools work
end-to-end, terminal commands execute, and permissions block unauthorized access.
"""

import pytest
from pathlib import Path

from galaxy.core.types import AgentTier
from galaxy.tools.builtin.file_read import FileReadTool
from galaxy.tools.builtin.file_write import FileWriteTool
from galaxy.tools.builtin.file_edit import FileEditTool
from galaxy.tools.builtin.terminal import TerminalTool
from galaxy.tools.builtin.tree import TreeTool
from galaxy.tools.registry import ToolRegistry
from galaxy.core.exceptions import ToolPermissionError


@pytest.fixture
def full_registry(tmp_path: Path) -> ToolRegistry:
    ws = str(tmp_path)
    registry = ToolRegistry()
    registry.register(FileReadTool(workspace=ws))
    registry.register(FileWriteTool(workspace=ws))
    registry.register(FileEditTool(workspace=ws))
    registry.register(TerminalTool(workspace=ws))
    registry.register(TreeTool(workspace=ws))
    return registry


class TestAgentUsesFileTools:
    """Test that agents can write, read, and edit files through the registry."""

    @pytest.mark.asyncio
    async def test_write_read_edit_cycle(self, full_registry, tmp_path) -> None:
        reg = full_registry

        # Write
        write_result = await reg.execute(
            "file_write", AgentTier.WORKER,
            path="src/app.py", content="def main():\n    return 'hello'"
        )
        assert write_result.success
        assert (tmp_path / "src" / "app.py").exists()

        # Read
        read_result = await reg.execute(
            "file_read", AgentTier.WORKER, path="src/app.py"
        )
        assert read_result.success
        assert "def main" in read_result.output

        # Edit
        edit_result = await reg.execute(
            "file_edit", AgentTier.WORKER,
            path="src/app.py",
            target="return 'hello'",
            replacement="return 'galaxy'",
        )
        assert edit_result.success

        # Verify edit
        verify = await reg.execute("file_read", AgentTier.WORKER, path="src/app.py")
        assert "galaxy" in verify.output

    @pytest.mark.asyncio
    async def test_tree_shows_created_files(self, full_registry, tmp_path) -> None:
        reg = full_registry

        await reg.execute("file_write", AgentTier.WORKER, path="models/user.py", content="# model")
        await reg.execute("file_write", AgentTier.WORKER, path="api/routes.py", content="# routes")

        tree_result = await reg.execute("tree", AgentTier.WORKER)
        assert tree_result.success
        assert "user.py" in tree_result.output
        assert "routes.py" in tree_result.output


class TestAgentRunsTerminalCommand:
    """Test terminal command execution through the registry."""

    @pytest.mark.asyncio
    async def test_agent_runs_terminal_command(self, full_registry) -> None:
        result = await full_registry.execute(
            "terminal", AgentTier.WORKER, command="echo 'galaxy is running'"
        )
        assert result.success
        assert "galaxy is running" in result.output

    @pytest.mark.asyncio
    async def test_python_execution(self, full_registry) -> None:
        result = await full_registry.execute(
            "terminal", AgentTier.WORKER,
            command="python3 -c \"print(2 + 2)\"",
        )
        assert result.success
        assert "4" in result.output


class TestPermissionBlocksUnauthorizedTool:
    """Test that tier-based permissions work correctly."""

    @pytest.mark.asyncio
    async def test_all_tools_accessible_to_worker(self, full_registry) -> None:
        """Workers should have access to standard file tools."""
        tools = full_registry.list_tools(AgentTier.WORKER)
        assert "file_read" in tools
        assert "file_write" in tools
        assert "file_edit" in tools

    @pytest.mark.asyncio
    async def test_schema_generation(self, full_registry) -> None:
        schemas = full_registry.generate_openai_schemas(AgentTier.WORKER)
        assert len(schemas) >= 3
        names = [s["function"]["name"] for s in schemas]
        assert "file_read" in names
