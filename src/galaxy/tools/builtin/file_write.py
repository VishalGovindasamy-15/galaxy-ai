"""FileWrite tool — write/create files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from galaxy.core.types import ToolResult
from galaxy.tools.base import BaseTool, ToolDefinition, ToolParameter


class FileWriteTool(BaseTool):
    """Write content to a file, creating directories as needed."""

    def __init__(self, workspace: str = ".") -> None:
        self._workspace = Path(workspace).resolve()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="file_write",
            description="Write content to a file. Creates parent directories if they don't exist.",
            parameters=[
                ToolParameter(name="path", type="string", description="File path relative to workspace"),
                ToolParameter(name="content", type="string", description="File contents to write"),
                ToolParameter(name="overwrite", type="boolean", description="Overwrite existing file", required=False),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        path = kwargs.get("path", "")
        content = kwargs.get("content", "")
        overwrite = kwargs.get("overwrite", True)

        full_path = (self._workspace / path).resolve()

        # Security: prevent writing outside workspace
        if not str(full_path).startswith(str(self._workspace)):
            return ToolResult(
                success=False,
                error=f"Path '{path}' is outside workspace. Blocked.",
            )

        if full_path.exists() and not overwrite:
            return ToolResult(
                success=False,
                error=f"File already exists: {path}. Set overwrite=true to replace.",
            )

        try:
            # Create directories
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            full_path.write_text(content, encoding="utf-8")

            return ToolResult(
                success=True,
                output=f"Written {len(content)} bytes to {path}",
                metadata={
                    "path": str(path),
                    "bytes": len(content),
                    "lines": content.count("\n") + 1,
                    "created_dirs": not full_path.parent.exists(),
                },
            )
        except PermissionError:
            return ToolResult(success=False, error=f"Permission denied: {path}")
        except OSError as e:
            return ToolResult(success=False, error=f"Write failed: {e}")
