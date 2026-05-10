"""FileEdit tool — search and replace within files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from galaxy.core.types import ToolResult
from galaxy.tools.base import BaseTool, ToolDefinition, ToolParameter


class FileEditTool(BaseTool):
    """Edit a file by replacing specific content."""

    def __init__(self, workspace: str = ".") -> None:
        self._workspace = Path(workspace).resolve()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="file_edit",
            description="Edit a file by replacing a target string with replacement content.",
            parameters=[
                ToolParameter(name="path", type="string", description="File path relative to workspace"),
                ToolParameter(name="target", type="string", description="Exact text to find and replace"),
                ToolParameter(name="replacement", type="string", description="Text to replace the target with"),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        path = kwargs.get("path", "")
        target = kwargs.get("target", "")
        replacement = kwargs.get("replacement", "")

        full_path = (self._workspace / path).resolve()

        if not str(full_path).startswith(str(self._workspace)):
            return ToolResult(success=False, error=f"Path '{path}' is outside workspace")

        if not full_path.exists():
            return ToolResult(success=False, error=f"File not found: {path}")

        try:
            content = full_path.read_text(encoding="utf-8")

            if target not in content:
                return ToolResult(
                    success=False,
                    error=f"Target text not found in {path}",
                    metadata={"path": str(path)},
                )

            count = content.count(target)
            new_content = content.replace(target, replacement)
            full_path.write_text(new_content, encoding="utf-8")

            return ToolResult(
                success=True,
                output=f"Replaced {count} occurrence(s) in {path}",
                metadata={"path": str(path), "replacements": count},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Edit failed: {e}")
