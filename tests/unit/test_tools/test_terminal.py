"""Tests for galaxy.tools.builtin.terminal."""

import pytest

from galaxy.tools.builtin.terminal import TerminalTool


class TestTerminalTool:
    """Test terminal command execution."""

    @pytest.mark.asyncio
    async def test_execute_command(self, tmp_path) -> None:
        tool = TerminalTool(workspace=str(tmp_path))
        result = await tool.execute(command="echo 'hello galaxy'")
        assert result.success
        assert "hello galaxy" in result.output

    @pytest.mark.asyncio
    async def test_execute_returns_output(self, tmp_path) -> None:
        tool = TerminalTool(workspace=str(tmp_path))
        result = await tool.execute(command="python3 -c \"print(1+1)\"")
        assert result.success
        assert "2" in result.output

    @pytest.mark.asyncio
    async def test_timeout(self, tmp_path) -> None:
        tool = TerminalTool(workspace=str(tmp_path), timeout=1)
        result = await tool.execute(command="sleep 10", timeout=1)
        assert not result.success
        assert "timed out" in result.error

    @pytest.mark.asyncio
    async def test_blocked_dangerous(self, tmp_path) -> None:
        tool = TerminalTool(workspace=str(tmp_path))
        result = await tool.execute(command="rm -rf /")
        assert not result.success
        assert "Blocked" in result.error

    @pytest.mark.asyncio
    async def test_blocked_shutdown(self, tmp_path) -> None:
        tool = TerminalTool(workspace=str(tmp_path))
        result = await tool.execute(command="shutdown -h now")
        assert not result.success
        assert "Blocked" in result.error

    @pytest.mark.asyncio
    async def test_failed_command(self, tmp_path) -> None:
        tool = TerminalTool(workspace=str(tmp_path))
        result = await tool.execute(command="false")
        assert not result.success

    @pytest.mark.asyncio
    async def test_pwd_in_workspace(self, tmp_path) -> None:
        tool = TerminalTool(workspace=str(tmp_path))
        result = await tool.execute(command="pwd")
        assert result.success
        assert str(tmp_path) in result.output
