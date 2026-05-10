"""Tests for galaxy.tools.builtin file tools."""

import pytest
from pathlib import Path

from galaxy.tools.builtin.file_read import FileReadTool
from galaxy.tools.builtin.file_write import FileWriteTool
from galaxy.tools.builtin.file_edit import FileEditTool


class TestFileRead:
    """Test FileReadTool."""

    @pytest.mark.asyncio
    async def test_read_full_file(self, tmp_path: Path) -> None:
        (tmp_path / "hello.txt").write_text("line1\nline2\nline3")
        tool = FileReadTool(workspace=str(tmp_path))
        result = await tool.execute(path="hello.txt")
        assert result.success
        assert "line1" in result.output
        assert "line3" in result.output

    @pytest.mark.asyncio
    async def test_read_line_range(self, tmp_path: Path) -> None:
        (tmp_path / "data.txt").write_text("a\nb\nc\nd\ne")
        tool = FileReadTool(workspace=str(tmp_path))
        result = await tool.execute(path="data.txt", start_line=2, end_line=4)
        assert result.success
        assert "b" in result.output
        assert "d" in result.output
        assert "a" not in result.output

    @pytest.mark.asyncio
    async def test_read_nonexistent(self, tmp_path: Path) -> None:
        tool = FileReadTool(workspace=str(tmp_path))
        result = await tool.execute(path="missing.txt")
        assert not result.success
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_read_outside_workspace(self, tmp_path: Path) -> None:
        tool = FileReadTool(workspace=str(tmp_path))
        result = await tool.execute(path="../../etc/passwd")
        assert not result.success
        assert "outside workspace" in result.error


class TestFileWrite:
    """Test FileWriteTool."""

    @pytest.mark.asyncio
    async def test_write_new(self, tmp_path: Path) -> None:
        tool = FileWriteTool(workspace=str(tmp_path))
        result = await tool.execute(path="new.py", content="print('hello')")
        assert result.success
        assert (tmp_path / "new.py").read_text() == "print('hello')"

    @pytest.mark.asyncio
    async def test_creates_directories(self, tmp_path: Path) -> None:
        tool = FileWriteTool(workspace=str(tmp_path))
        result = await tool.execute(path="src/deep/nested/file.py", content="# code")
        assert result.success
        assert (tmp_path / "src/deep/nested/file.py").exists()

    @pytest.mark.asyncio
    async def test_overwrite(self, tmp_path: Path) -> None:
        (tmp_path / "existing.txt").write_text("old content")
        tool = FileWriteTool(workspace=str(tmp_path))
        result = await tool.execute(path="existing.txt", content="new content", overwrite=True)
        assert result.success
        assert (tmp_path / "existing.txt").read_text() == "new content"

    @pytest.mark.asyncio
    async def test_no_overwrite_existing(self, tmp_path: Path) -> None:
        (tmp_path / "existing.txt").write_text("keep this")
        tool = FileWriteTool(workspace=str(tmp_path))
        result = await tool.execute(path="existing.txt", content="replace", overwrite=False)
        assert not result.success
        assert "already exists" in result.error

    @pytest.mark.asyncio
    async def test_blocked_outside_workspace(self, tmp_path: Path) -> None:
        tool = FileWriteTool(workspace=str(tmp_path))
        result = await tool.execute(path="../../etc/evil", content="bad")
        assert not result.success
        assert "outside workspace" in result.error


class TestFileEdit:
    """Test FileEditTool."""

    @pytest.mark.asyncio
    async def test_replace_content(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text("def hello():\n    return 'world'")
        tool = FileEditTool(workspace=str(tmp_path))
        result = await tool.execute(
            path="app.py",
            target="return 'world'",
            replacement="return 'galaxy'",
        )
        assert result.success
        assert "return 'galaxy'" in (tmp_path / "app.py").read_text()

    @pytest.mark.asyncio
    async def test_nonexistent_file(self, tmp_path: Path) -> None:
        tool = FileEditTool(workspace=str(tmp_path))
        result = await tool.execute(path="missing.py", target="x", replacement="y")
        assert not result.success
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_target_not_found(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text("def hello(): pass")
        tool = FileEditTool(workspace=str(tmp_path))
        result = await tool.execute(path="app.py", target="nonexistent text", replacement="new")
        assert not result.success
        assert "not found" in result.error
