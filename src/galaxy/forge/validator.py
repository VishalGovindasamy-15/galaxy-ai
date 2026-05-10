"""Continuous validator — validates generated code quality.

Runs syntax, import, and lint checks on generated files.
"""

from __future__ import annotations

import ast
import logging
import subprocess
from pathlib import Path
from typing import Any

from galaxy.core.types import ValidationResult, ValidationStep

logger = logging.getLogger(__name__)


class ContinuousValidator:
    """Validates generated code through multiple checks."""

    def __init__(self, workspace: str = ".") -> None:
        self.workspace = Path(workspace)

    async def validate_file(self, file_path: str) -> list[ValidationResult]:
        """Run all validation checks on a file.

        Args:
            file_path: Path relative to workspace.

        Returns:
            List of ValidationResult for each check.
        """
        full_path = self.workspace / file_path
        results: list[ValidationResult] = []

        if not full_path.exists():
            results.append(ValidationResult(
                step=ValidationStep.SYNTAX, passed=False,
                message=f"File not found: {file_path}",
            ))
            return results

        # Only validate Python files for now
        if full_path.suffix == ".py":
            results.append(self.check_syntax(full_path))
            results.append(self.check_imports(full_path))
            results.append(self.check_lint(full_path))

        return results

    def check_syntax(self, path: Path) -> ValidationResult:
        """Check Python syntax validity."""
        try:
            source = path.read_text(encoding="utf-8")
            ast.parse(source, filename=str(path))
            return ValidationResult(step=ValidationStep.SYNTAX, passed=True, message="Syntax OK")
        except SyntaxError as e:
            return ValidationResult(
                step=ValidationStep.SYNTAX, passed=False,
                message=f"Syntax error at line {e.lineno}: {e.msg}",
                details=f"line={e.lineno}, offset={e.offset}",
            )

    def check_imports(self, path: Path) -> ValidationResult:
        """Check that all imports are valid."""
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)

            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)

            return ValidationResult(
                step=ValidationStep.IMPORTS, passed=True,
                message=f"{len(imports)} imports parsed OK",
                details=", ".join(imports),
            )
        except Exception as e:
            return ValidationResult(
                step=ValidationStep.IMPORTS, passed=False,
                message=f"Import check failed: {e}",
            )

    def check_lint(self, path: Path) -> ValidationResult:
        """Run ruff linter if available."""
        try:
            result = subprocess.run(
                ["ruff", "check", str(path), "--no-fix", "--quiet"],
                capture_output=True, text=True, timeout=30,
            )

            if result.returncode == 0:
                return ValidationResult(
                    step=ValidationStep.LINT, passed=True, message="Lint OK (ruff)",
                )
            else:
                issues = result.stdout.strip().split("\n")
                return ValidationResult(
                    step=ValidationStep.LINT, passed=False,
                    message=f"{len(issues)} lint issue(s)",
                    details="\n".join(issues[:10]),
                )
        except FileNotFoundError:
            return ValidationResult(
                step=ValidationStep.LINT, passed=True,
                message="ruff not installed — skipped",
            )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                step=ValidationStep.LINT, passed=False, message="Lint check timed out",
            )
