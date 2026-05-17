"""Tests for galaxy.project.reconstructor."""

from pathlib import Path

from galaxy.project.reconstructor import ProjectReconstructor
from galaxy.project.spec import FileSpec, FileStatus, ProjectSpec


class TestProjectReconstructor:
    def test_analyze_empty_workspace(self, tmp_path: Path) -> None:
        spec = ProjectSpec(name="test")
        spec.add_file(FileSpec(path="main.py", domain="backend"))

        recon = ProjectReconstructor(workspace=tmp_path)
        report = recon.analyze(spec)

        assert len(report.missing) == 1
        assert "main.py" in report.missing

    def test_analyze_complete_workspace(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("def main(): pass")

        spec = ProjectSpec(name="test")
        spec.add_file(FileSpec(path="main.py", symbols=["main"]))

        recon = ProjectReconstructor(workspace=tmp_path)
        report = recon.analyze(spec)

        assert len(report.missing) == 0
        assert len(report.present) == 1
        assert report.is_complete

    def test_analyze_missing_symbols(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("def main(): pass")

        spec = ProjectSpec(name="test")
        spec.add_file(FileSpec(path="main.py", symbols=["main", "missing_func"]))

        recon = ProjectReconstructor(workspace=tmp_path)
        report = recon.analyze(spec)

        assert len(report.modified) == 1
        assert "missing_func" in report.modified[0].reason

    def test_analyze_extra_files(self, tmp_path: Path) -> None:
        (tmp_path / "extra.py").write_text("x = 1")

        spec = ProjectSpec(name="test")
        recon = ProjectReconstructor(workspace=tmp_path)
        report = recon.analyze(spec)

        assert len(report.extra) >= 1

    def test_rebuild_structure(self, tmp_path: Path) -> None:
        spec = ProjectSpec(name="test")
        spec.add_file(FileSpec(path="src/auth/service.py"))
        spec.add_file(FileSpec(path="src/models/user.py"))

        recon = ProjectReconstructor(workspace=tmp_path)
        created = recon.rebuild_structure(spec)

        assert (tmp_path / "src" / "auth").is_dir()
        assert (tmp_path / "src" / "models").is_dir()

    def test_get_rebuild_plan(self, tmp_path: Path) -> None:
        (tmp_path / "existing.py").write_text("def foo(): pass")

        spec = ProjectSpec(name="test")
        spec.add_file(FileSpec(path="existing.py", symbols=["foo"]))
        spec.add_file(FileSpec(path="missing.py", symbols=["bar"]))

        recon = ProjectReconstructor(workspace=tmp_path)
        plan = recon.get_rebuild_plan(spec)

        assert len(plan) == 1
        assert plan[0].path == "missing.py"

    def test_write_stub(self, tmp_path: Path) -> None:
        spec = FileSpec(
            path="auth/service.py",
            description="Auth service",
            domain="auth",
            symbols=["login", "logout"],
        )

        recon = ProjectReconstructor(workspace=tmp_path)
        path = recon.write_stub(spec)

        assert path.exists()
        content = path.read_text()
        assert "Auth service" in content
        assert "login" in content

    def test_report_summary(self, tmp_path: Path) -> None:
        spec = ProjectSpec(name="test")
        spec.add_file(FileSpec(path="a.py"))
        spec.add_file(FileSpec(path="b.py"))

        recon = ProjectReconstructor(workspace=tmp_path)
        report = recon.analyze(spec)

        summary = report.summary()
        assert "Missing: 2" in summary

    def test_report_total_issues(self, tmp_path: Path) -> None:
        spec = ProjectSpec(name="test")
        spec.add_file(FileSpec(path="a.py"))

        recon = ProjectReconstructor(workspace=tmp_path)
        report = recon.analyze(spec)
        assert report.total_issues == 1
