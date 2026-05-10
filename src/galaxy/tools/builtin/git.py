"""Git tool — git operations within the workspace."""

from __future__ import annotations

import asyncio
from typing import Any

from galaxy.core.types import ToolResult
from galaxy.tools.base import BaseTool, ToolDefinition, ToolParameter


class GitTool(BaseTool):
    """Execute git operations."""

    def __init__(self, workspace: str = ".") -> None:
        self._workspace = workspace

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="git",
            description="Execute git commands (status, diff, log, add, commit).",
            parameters=[
                ToolParameter(name="command", type="string",
                              description="Git subcommand and args (e.g., 'status', 'diff src/', 'log -5')"),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        command = kwargs.get("command", "")

        # Block destructive operations
        blocked = ["push", "force", "reset --hard", "clean -fd"]
        for b in blocked:
            if b in command:
                return ToolResult(success=False, error=f"Blocked git operation: {b}")

        try:
            proc = await asyncio.create_subprocess_shell(
                f"git {command}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self._workspace,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

            output = stdout.decode("utf-8", errors="replace").strip()
            error = stderr.decode("utf-8", errors="replace").strip()

            return ToolResult(
                success=proc.returncode == 0,
                output=output[:5000],
                error=error if proc.returncode != 0 else "",
                metadata={"command": f"git {command}"},
            )
        except asyncio.TimeoutError:
            return ToolResult(success=False, error="Git command timed out")
        except FileNotFoundError:
            return ToolResult(success=False, error="git not available")
