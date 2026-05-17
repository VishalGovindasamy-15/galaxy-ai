"""Tests for galaxy.project.analyzer."""

from pathlib import Path

from galaxy.project.analyzer import ProjectAnalyzer
from galaxy.project.spec import FileStatus


class TestProjectAnalyzer:
    def test_analyze_empty(self, tmp_path: Path) -> None:
        analyzer = ProjectAnalyzer(workspace=tmp_path)
        spec = analyzer.analyze(name="empty")
        assert spec.name == "empty"
        assert spec.file_count == 0

    def test_analyze_python_project(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()")
        (tmp_path / "models.py").write_text("class User:\n    pass")
        (tmp_path / "requirements.txt").write_text("fastapi\nsqlalchemy\n")

        analyzer = ProjectAnalyzer(workspace=tmp_path)
        spec = analyzer.analyze()

        assert spec.file_count >= 2
        assert "Python" in spec.tech_stack or "FastAPI" in spec.tech_stack
        assert spec.project_type in ("REST API", "Python Application")

    def test_detect_tech_stack(self, tmp_path: Path) -> None:
        (tmp_path / "requirements.txt").write_text("fastapi\n")
        (tmp_path / "Dockerfile").write_text("FROM python:3.12\n")

        analyzer = ProjectAnalyzer(workspace=tmp_path)
        spec = analyzer.analyze()

        assert "Python" in spec.tech_stack
        assert "Docker" in spec.tech_stack

    def test_classify_domains(self, tmp_path: Path) -> None:
        (tmp_path / "auth").mkdir()
        (tmp_path / "auth" / "service.py").write_text("def login(): pass")
        (tmp_path / "models.py").write_text("class User: pass")
        (tmp_path / "test_main.py").write_text("def test_foo(): pass")

        analyzer = ProjectAnalyzer(workspace=tmp_path)
        spec = analyzer.analyze()

        domains = {d.name for d in spec.domains}
        assert "auth" in domains or "testing" in domains

    def test_extract_symbols(self, tmp_path: Path) -> None:
        (tmp_path / "utils.py").write_text(
            "def add(a, b):\n    return a + b\n\nclass Calculator:\n    pass"
        )

        analyzer = ProjectAnalyzer(workspace=tmp_path)
        spec = analyzer.analyze()

        file_spec = spec.get_file("utils.py")
        assert file_spec is not None
        assert "add" in file_spec.symbols
        assert "Calculator" in file_spec.symbols

    def test_skips_venv(self, tmp_path: Path) -> None:
        (tmp_path / ".venv" / "lib").mkdir(parents=True)
        (tmp_path / ".venv" / "lib" / "module.py").write_text("x = 1")
        (tmp_path / "app.py").write_text("x = 1")

        analyzer = ProjectAnalyzer(workspace=tmp_path)
        spec = analyzer.analyze()

        paths = [f.path for f in spec.files]
        assert all(".venv" not in p for p in paths)
        assert "app.py" in paths

    def test_existing_files_are_integrated(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("x = 1")

        analyzer = ProjectAnalyzer(workspace=tmp_path)
        spec = analyzer.analyze()

        assert spec.files[0].status == FileStatus.INTEGRATED

    def test_progress_calculation(self, tmp_path: Path) -> None:
        (tmp_path / "a.py").write_text("x = 1")
        (tmp_path / "b.py").write_text("y = 2")

        analyzer = ProjectAnalyzer(workspace=tmp_path)
        spec = analyzer.analyze()

        # All existing files are INTEGRATED, so progress should be 1.0
        assert spec.progress == 1.0

    def test_default_name_from_dir(self, tmp_path: Path) -> None:
        analyzer = ProjectAnalyzer(workspace=tmp_path)
        spec = analyzer.analyze()
        assert spec.name == tmp_path.name
