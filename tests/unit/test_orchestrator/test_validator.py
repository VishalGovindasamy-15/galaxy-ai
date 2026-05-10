"""Tests for galaxy.forge.validator."""

import pytest
from pathlib import Path

from galaxy.core.types import ValidationStep
from galaxy.forge.validator import ContinuousValidator


class TestSyntaxCheck:
    """Test syntax validation."""

    def test_valid_python(self, tmp_path: Path) -> None:
        (tmp_path / "good.py").write_text("def hello():\n    return 42\n")
        v = ContinuousValidator(workspace=str(tmp_path))
        result = v.check_syntax(tmp_path / "good.py")
        assert result.passed
        assert result.step == ValidationStep.SYNTAX

    def test_invalid_python(self, tmp_path: Path) -> None:
        (tmp_path / "bad.py").write_text("def hello(\n    return 42\n")
        v = ContinuousValidator(workspace=str(tmp_path))
        result = v.check_syntax(tmp_path / "bad.py")
        assert not result.passed
        assert "Syntax error" in result.message


class TestImportCheck:
    """Test import validation."""

    def test_valid_imports(self, tmp_path: Path) -> None:
        (tmp_path / "mod.py").write_text("import os\nfrom pathlib import Path\n")
        v = ContinuousValidator(workspace=str(tmp_path))
        result = v.check_imports(tmp_path / "mod.py")
        assert result.passed
        assert "2 imports" in result.message


class TestLintCheck:
    """Test lint validation."""

    def test_clean_file(self, tmp_path: Path) -> None:
        (tmp_path / "clean.py").write_text('"""Clean module."""\n\nx = 1\n')
        v = ContinuousValidator(workspace=str(tmp_path))
        result = v.check_lint(tmp_path / "clean.py")
        assert result.step == ValidationStep.LINT


class TestValidateFile:
    """Test full file validation."""

    @pytest.mark.asyncio
    async def test_validate_existing_file(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text("def main():\n    pass\n")
        v = ContinuousValidator(workspace=str(tmp_path))
        results = await v.validate_file("app.py")
        assert len(results) >= 2
        assert results[0].step == ValidationStep.SYNTAX

    @pytest.mark.asyncio
    async def test_validate_missing_file(self, tmp_path: Path) -> None:
        v = ContinuousValidator(workspace=str(tmp_path))
        results = await v.validate_file("missing.py")
        assert len(results) == 1
        assert not results[0].passed
