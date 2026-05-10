"""Tests for galaxy.tools.builtin.tree."""

import pytest
from pathlib import Path

from galaxy.tools.builtin.tree import TreeTool


class TestTreeTool:
    """Test tree display tool."""

    @pytest.mark.asyncio
    async def test_tree_display(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("# main")
        (tmp_path / "README.md").write_text("# readme")

        tool = TreeTool(workspace=str(tmp_path))
        result = await tool.execute()
        assert result.success
        assert "main.py" in result.output
        assert "README.md" in result.output

    @pytest.mark.asyncio
    async def test_tree_ignores_pycache(self, tmp_path: Path) -> None:
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "cache.pyc").write_text("x")
        (tmp_path / "real.py").write_text("# real")

        tool = TreeTool(workspace=str(tmp_path))
        result = await tool.execute()
        assert result.success
        assert "__pycache__" not in result.output
        assert "real.py" in result.output

    @pytest.mark.asyncio
    async def test_tree_outside_workspace(self, tmp_path: Path) -> None:
        tool = TreeTool(workspace=str(tmp_path))
        result = await tool.execute(path="../../../")
        assert not result.success
