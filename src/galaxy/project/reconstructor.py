"""Project reconstructor — rebuild project from spec.

Given a ProjectSpec, reconstructs the project directory structure
and regenerates missing files using the contract system.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from galaxy.project.spec import FileSpec, FileStatus, ProjectSpec

logger = logging.getLogger(__name__)


class ProjectReconstructor:
    """Reconstructs a project from its ProjectSpec.

    Can rebuild directory structure, identify missing files,
    and generate a rebuild plan.

    Usage:
        reconstructor = ProjectReconstructor(workspace=Path("."))
        report = reconstructor.analyze(spec)
        reconstructor.rebuild_structure(spec)
    """

    def __init__(self, workspace: Path) -> None:
        self._workspace = workspace

    def analyze(self, spec: ProjectSpec) -> ReconstructionReport:
        """Analyze current workspace against the spec.

        Args:
            spec: The project specification.

        Returns:
            ReconstructionReport with missing/modified/extra files.
        """
        report = ReconstructionReport()

        for file_spec in spec.files:
            path = self._workspace / file_spec.path
            if path.exists():
                # Check if file has expected symbols
                actual_symbols = self._extract_symbols(path)
                missing = [s for s in file_spec.symbols if s not in actual_symbols]
                if missing:
                    report.modified.append(FileDiscrepancy(
                        path=file_spec.path,
                        reason=f"Missing symbols: {', '.join(missing)}",
                        expected_symbols=file_spec.symbols,
                        actual_symbols=actual_symbols,
                    ))
                else:
                    report.present.append(file_spec.path)
            else:
                report.missing.append(file_spec.path)

        # Find extra files not in spec
        spec_paths = {f.path for f in spec.files}
        for path in self._scan_workspace():
            if path not in spec_paths:
                report.extra.append(path)

        return report

    def rebuild_structure(self, spec: ProjectSpec) -> list[Path]:
        """Rebuild directory structure from spec (directories only).

        Creates all required directories for the project files.
        Does NOT generate file contents.

        Args:
            spec: The project specification.

        Returns:
            List of created directories.
        """
        created: list[Path] = []

        for file_spec in spec.files:
            dir_path = (self._workspace / file_spec.path).parent
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                if dir_path not in created:
                    created.append(dir_path)

        return created

    def get_rebuild_plan(self, spec: ProjectSpec) -> list[FileSpec]:
        """Get list of files that need to be regenerated.

        Args:
            spec: The project specification.

        Returns:
            List of FileSpecs for files needing regeneration.
        """
        report = self.analyze(spec)
        to_rebuild: list[FileSpec] = []

        for missing_path in report.missing:
            file_spec = spec.get_file(missing_path)
            if file_spec:
                to_rebuild.append(file_spec)

        for discrepancy in report.modified:
            file_spec = spec.get_file(discrepancy.path)
            if file_spec:
                to_rebuild.append(file_spec)

        return to_rebuild

    def write_stub(self, file_spec: FileSpec) -> Path:
        """Write a stub file with placeholder content.

        Args:
            file_spec: The file specification.

        Returns:
            Path to the created stub.
        """
        path = self._workspace / file_spec.path
        path.parent.mkdir(parents=True, exist_ok=True)

        stub_lines = [
            f'"""Stub: {file_spec.description}"""',
            "",
            f"# Domain: {file_spec.domain}",
            f"# Status: {file_spec.status.value}",
        ]

        if file_spec.symbols:
            stub_lines.append("")
            stub_lines.append("# Expected symbols:")
            for symbol in file_spec.symbols:
                stub_lines.append(f"#   - {symbol}")

        stub_lines.append("")
        path.write_text("\n".join(stub_lines))
        return path

    def _extract_symbols(self, path: Path) -> list[str]:
        """Extract function and class names from a file."""
        import re
        symbols = []
        try:
            content = path.read_text()[:5000]
            symbols.extend(re.findall(r"^(?:async\s+)?def\s+(\w+)", content, re.MULTILINE))
            symbols.extend(re.findall(r"^class\s+(\w+)", content, re.MULTILINE))
        except (OSError, UnicodeDecodeError):
            pass
        return symbols

    def _scan_workspace(self) -> list[str]:
        """Scan workspace for source files."""
        extensions = {".py", ".ts", ".tsx", ".js", ".jsx"}
        skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", ".galaxy"}
        files: list[str] = []

        try:
            for path in self._workspace.rglob("*"):
                if path.is_file() and path.suffix in extensions:
                    if not any(s in path.parts for s in skip_dirs):
                        files.append(str(path.relative_to(self._workspace)))
        except OSError:
            pass

        return sorted(files)


class FileDiscrepancy:
    """Describes a discrepancy between spec and actual file."""

    def __init__(
        self,
        path: str = "",
        reason: str = "",
        expected_symbols: list[str] | None = None,
        actual_symbols: list[str] | None = None,
    ) -> None:
        self.path = path
        self.reason = reason
        self.expected_symbols = expected_symbols or []
        self.actual_symbols = actual_symbols or []


class ReconstructionReport:
    """Report from analyzing workspace against spec."""

    def __init__(self) -> None:
        self.present: list[str] = []
        self.missing: list[str] = []
        self.modified: list[FileDiscrepancy] = []
        self.extra: list[str] = []

    @property
    def is_complete(self) -> bool:
        return len(self.missing) == 0 and len(self.modified) == 0

    @property
    def total_issues(self) -> int:
        return len(self.missing) + len(self.modified)

    def summary(self) -> str:
        return (
            f"Present: {len(self.present)}, "
            f"Missing: {len(self.missing)}, "
            f"Modified: {len(self.modified)}, "
            f"Extra: {len(self.extra)}"
        )
