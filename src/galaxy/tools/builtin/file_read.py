"""FileRead tool — read file contents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from galaxy.core.types import ToolResult
from galaxy.tools.base import BaseTool, ToolDefinition, ToolParameter


class FileReadTool(BaseTool):
    """Read contents of a file, optionally with line range."""

    def __init__(self, workspace: str = ".") -> None:
        self._workspace = Path(workspace).resolve()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="file_read",
            description="Read the contents of a file. Can read full file or a specific line range.",
            parameters=[
                ToolParameter(name="path", type="string", description="File path relative to workspace"),
                ToolParameter(name="start_line", type="integer", description="Start line (1-indexed)", required=False),
                ToolParameter(name="end_line", type="integer", description="End line (1-indexed, inclusive)", required=False),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        path = kwargs.get("path", "")
        start_line = kwargs.get("start_line")
        end_line = kwargs.get("end_line")

        full_path = (self._workspace / path).resolve()

        # Security: prevent reading outside workspace
        if not str(full_path).startswith(str(self._workspace)):
            return ToolResult(
                success=False,
                error=f"Path '{path}' is outside workspace",
            )

        if not full_path.exists():
            return ToolResult(success=False, error=f"File not found: {path}")

        if not full_path.is_file():
            return ToolResult(success=False, error=f"Not a file: {path}")

        try:
            content = full_path.read_text(encoding="utf-8")

            if start_line is not None or end_line is not None:
                lines = content.split("\n")
                start = max(1, start_line or 1) - 1  # Convert to 0-indexed
                end = min(len(lines), end_line or len(lines))
                content = "\n".join(lines[start:end])

            return ToolResult(
                success=True,
                output=content,
                metadata={"path": str(path), "lines": content.count("\n") + 1},
            )
        except UnicodeDecodeError:
            return ToolResult(success=False, error=f"Cannot read binary file: {path}")
        except PermissionError:
            return ToolResult(success=False, error=f"Permission denied: {path}")
