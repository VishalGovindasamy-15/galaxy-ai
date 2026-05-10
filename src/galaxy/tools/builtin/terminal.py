"""Terminal tool — execute shell commands."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from galaxy.core.types import AgentTier, ToolResult
from galaxy.tools.base import BaseTool, ToolDefinition, ToolParameter

logger = logging.getLogger(__name__)

# Commands that should NEVER be executed
BLOCKED_COMMANDS = [
    "rm -rf /", "rm -rf /*", "mkfs", "dd if=/dev/zero",
    ":(){:|:&};:", "chmod -R 777 /", "wget", "curl -o",
    "shutdown", "reboot", "halt", "poweroff",
]

# Commands allowed for workers (restrictive)
WORKER_ALLOWED_PREFIXES = [
    "python", "pip", "npm", "node", "cargo", "go ",
    "pytest", "mypy", "ruff", "black", "isort",
    "ls", "cat", "head", "tail", "wc", "grep", "find",
    "echo", "pwd", "which", "env", "git ",
]


class TerminalTool(BaseTool):
    """Execute shell commands with safety controls."""

    def __init__(self, workspace: str = ".", timeout: int = 60) -> None:
        self._workspace = workspace
        self._timeout = timeout

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="terminal",
            description="Execute a shell command in the workspace directory.",
            parameters=[
                ToolParameter(name="command", type="string", description="Shell command to execute"),
                ToolParameter(name="timeout", type="integer", description="Timeout in seconds", required=False),
            ],
            dangerous=True,
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        command = kwargs.get("command", "")
        timeout = kwargs.get("timeout", self._timeout)

        # Security: block dangerous commands
        blocked = self._is_blocked(command)
        if blocked:
            return ToolResult(
                success=False,
                error=f"Blocked dangerous command: {blocked}",
            )

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self._workspace,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    error=f"Command timed out after {timeout}s: {command[:100]}",
                )

            stdout_str = stdout.decode("utf-8", errors="replace").strip()
            stderr_str = stderr.decode("utf-8", errors="replace").strip()

            # Truncate long output
            max_output = 10000
            if len(stdout_str) > max_output:
                stdout_str = stdout_str[:max_output] + f"\n... (truncated, {len(stdout_str)} total chars)"

            success = process.returncode == 0
            output = stdout_str
            if stderr_str and not success:
                output = f"STDOUT:\n{stdout_str}\n\nSTDERR:\n{stderr_str}" if stdout_str else stderr_str

            return ToolResult(
                success=success,
                output=output,
                error=stderr_str if not success else "",
                metadata={
                    "command": command,
                    "return_code": process.returncode,
                    "stdout_lines": stdout_str.count("\n") + 1 if stdout_str else 0,
                },
            )

        except Exception as e:
            return ToolResult(success=False, error=f"Command execution failed: {e}")

    @staticmethod
    def _is_blocked(command: str) -> str | None:
        """Check if a command is blocked. Returns the matching blocked pattern or None."""
        cmd_lower = command.lower().strip()
        for blocked in BLOCKED_COMMANDS:
            if blocked in cmd_lower:
                return blocked
        return None
