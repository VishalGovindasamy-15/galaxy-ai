"""Tree tool — display directory structure."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from galaxy.core.types import ToolResult
from galaxy.tools.base import BaseTool, ToolDefinition, ToolParameter

IGNORE_DIRS = {
    "__pycache__", ".git", "node_modules", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist",
    "build", "*.egg-info", ".galaxy",
}


class TreeTool(BaseTool):
    """Display directory tree structure."""

    def __init__(self, workspace: str = ".") -> None:
        self._workspace = Path(workspace).resolve()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="tree",
            description="Display directory tree structure of the workspace.",
            parameters=[
                ToolParameter(name="path", type="string", description="Directory path", required=False),
                ToolParameter(name="max_depth", type="integer", description="Max depth to display", required=False),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        path = kwargs.get("path", ".")
        max_depth = kwargs.get("max_depth", 4)

        target = (self._workspace / path).resolve()
        if not str(target).startswith(str(self._workspace)):
            return ToolResult(success=False, error="Path outside workspace")

        if not target.is_dir():
            return ToolResult(success=False, error=f"Not a directory: {path}")

        lines: list[str] = []
        file_count = 0
        dir_count = 0

        def _walk(dir_path: Path, prefix: str, depth: int) -> None:
            nonlocal file_count, dir_count

            if depth > max_depth:
                return

            try:
                entries = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
            except PermissionError:
                return

            entries = [e for e in entries if e.name not in IGNORE_DIRS]

            for i, entry in enumerate(entries):
                is_last = i == len(entries) - 1
                connector = "└── " if is_last else "├── "
                child_prefix = "    " if is_last else "│   "

                if entry.is_dir():
                    dir_count += 1
                    lines.append(f"{prefix}{connector}{entry.name}/")
                    _walk(entry, prefix + child_prefix, depth + 1)
                else:
                    file_count += 1
                    lines.append(f"{prefix}{connector}{entry.name}")

        lines.append(f"{target.name}/")
        _walk(target, "", 1)
        lines.append(f"\n{dir_count} directories, {file_count} files")

        output = "\n".join(lines)
        return ToolResult(
            success=True,
            output=output,
            metadata={"directories": dir_count, "files": file_count},
        )
