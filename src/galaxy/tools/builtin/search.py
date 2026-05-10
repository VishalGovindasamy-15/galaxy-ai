"""Search tool — grep/search within the workspace."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from galaxy.core.types import ToolResult
from galaxy.tools.base import BaseTool, ToolDefinition, ToolParameter


class SearchTool(BaseTool):
    """Search for text patterns within workspace files."""

    def __init__(self, workspace: str = ".") -> None:
        self._workspace = Path(workspace).resolve()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="search",
            description="Search for a text pattern in workspace files using grep.",
            parameters=[
                ToolParameter(name="pattern", type="string", description="Text pattern to search for"),
                ToolParameter(name="path", type="string", description="Directory or file to search in", required=False),
                ToolParameter(name="case_sensitive", type="boolean", description="Case-sensitive search", required=False),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        pattern = kwargs.get("pattern", "")
        path = kwargs.get("path", ".")
        case_sensitive = kwargs.get("case_sensitive", True)

        search_path = (self._workspace / path).resolve()
        if not str(search_path).startswith(str(self._workspace)):
            return ToolResult(success=False, error="Path outside workspace")

        cmd_parts = ["grep", "-rn", "--include=*.py", "--include=*.ts", "--include=*.js",
                      "--include=*.yaml", "--include=*.yml", "--include=*.json",
                      "--include=*.md", "--include=*.toml", "--include=*.cfg"]

        if not case_sensitive:
            cmd_parts.append("-i")

        cmd_parts.extend([pattern, str(search_path)])

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
            output = stdout.decode("utf-8", errors="replace").strip()

            # Make paths relative
            output = output.replace(str(self._workspace) + "/", "")

            lines = output.split("\n") if output else []
            return ToolResult(
                success=True,
                output=output[:5000] if output else "No matches found",
                metadata={"matches": len(lines), "pattern": pattern},
            )
        except asyncio.TimeoutError:
            return ToolResult(success=False, error="Search timed out")
        except FileNotFoundError:
            return ToolResult(success=False, error="grep not available")
