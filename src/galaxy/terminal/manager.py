"""Terminal manager — manages tmux sessions for Galaxy.

Provides isolated terminal sessions for command execution,
with session lifecycle management and output capture.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from typing import Any

from galaxy.core.exceptions import SessionCreationError, TmuxNotInstalledError

logger = logging.getLogger(__name__)


class TerminalSession:
    """Represents a single tmux session."""

    def __init__(self, name: str, workspace: str = ".") -> None:
        self.name = name
        self.workspace = workspace
        self._alive = False

    @property
    def is_alive(self) -> bool:
        return self._alive

    async def create(self) -> None:
        """Create the tmux session."""
        proc = await asyncio.create_subprocess_exec(
            "tmux", "new-session", "-d", "-s", self.name, "-c", self.workspace,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            error = stderr.decode().strip()
            raise SessionCreationError(f"Failed to create tmux session '{self.name}': {error}")
        self._alive = True
        logger.debug("Created tmux session: %s", self.name)

    async def execute(self, command: str, timeout: int = 60) -> str:
        """Execute a command in this tmux session and capture output.

        Args:
            command: Shell command to execute.
            timeout: Maximum execution time in seconds.

        Returns:
            Command output as string.
        """
        # Use a marker to detect command completion
        marker = f"__GALAXY_DONE_{id(command)}__"
        full_cmd = f"{command}; echo '{marker}'"

        # Send command to tmux
        await asyncio.create_subprocess_exec(
            "tmux", "send-keys", "-t", self.name, full_cmd, "Enter",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Wait for completion by polling pane output
        output = ""
        elapsed = 0
        poll_interval = 0.5

        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            proc = await asyncio.create_subprocess_exec(
                "tmux", "capture-pane", "-t", self.name, "-p",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            output = stdout.decode("utf-8", errors="replace")

            if marker in output:
                # Remove marker and trailing content
                output = output[:output.rfind(marker)].strip()
                return output

        return output.strip()

    async def kill(self) -> None:
        """Kill the tmux session."""
        await asyncio.create_subprocess_exec(
            "tmux", "kill-session", "-t", self.name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._alive = False
        logger.debug("Killed tmux session: %s", self.name)


class TerminalManager:
    """Manages tmux sessions for Galaxy."""

    def __init__(self, workspace: str = ".") -> None:
        self.workspace = workspace
        self._sessions: dict[str, TerminalSession] = {}

    @staticmethod
    def is_tmux_installed() -> bool:
        """Check if tmux is available."""
        return shutil.which("tmux") is not None

    def ensure_tmux(self) -> None:
        """Ensure tmux is installed.

        Raises:
            TmuxNotInstalledError: If tmux is not found.
        """
        if not self.is_tmux_installed():
            raise TmuxNotInstalledError(
                "tmux is not installed. Run: sudo apt install tmux"
            )

    async def create_session(self, name: str) -> TerminalSession:
        """Create a new tmux session.

        Args:
            name: Session name.

        Returns:
            The created TerminalSession.
        """
        self.ensure_tmux()

        session = TerminalSession(name=name, workspace=self.workspace)
        await session.create()
        self._sessions[name] = session
        return session

    async def get_or_create(self, name: str) -> TerminalSession:
        """Get existing session or create new one."""
        if name in self._sessions and self._sessions[name].is_alive:
            return self._sessions[name]
        return await self.create_session(name)

    async def execute_in_session(
        self, session_name: str, command: str, timeout: int = 60,
    ) -> str:
        """Execute a command in a named session."""
        session = await self.get_or_create(session_name)
        return await session.execute(command, timeout)

    async def cleanup(self) -> None:
        """Kill all managed sessions."""
        for name, session in list(self._sessions.items()):
            try:
                await session.kill()
            except Exception:
                logger.warning("Failed to cleanup session: %s", name)
        self._sessions.clear()

    async def cleanup_session(self, name: str) -> bool:
        """Kill a specific session."""
        session = self._sessions.pop(name, None)
        if session:
            await session.kill()
            return True
        return False

    @property
    def active_sessions(self) -> list[str]:
        """List active session names."""
        return [n for n, s in self._sessions.items() if s.is_alive]
