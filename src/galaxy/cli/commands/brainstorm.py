"""Galaxy brainstorm CLI command — galaxy brainstorm."""

from __future__ import annotations

from pathlib import Path

from galaxy.cli.commands import run_brainstorm


def brainstorm_command(
    workspace: Path,
    prompt: str = "",
    mode: str = "structured",
    project_name: str = "",
) -> None:
    """Entry point for `galaxy brainstorm` command."""
    run_brainstorm(
        workspace=workspace,
        prompt=prompt,
        mode=mode,
        project_name=project_name,
    )
