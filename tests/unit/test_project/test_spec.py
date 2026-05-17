"""Tests for galaxy.project.spec."""

from galaxy.project.spec import (
    DomainSpec,
    FileSpec,
    FileStatus,
    ProjectSpec,
    ProjectStatus,
)


class TestFileSpec:
    def test_default(self) -> None:
        f = FileSpec()
        assert f.path == ""
        assert f.status == FileStatus.PLANNED

    def test_roundtrip(self) -> None:
        original = FileSpec(
            path="auth/service.py",
            domain="auth",
            status=FileStatus.GENERATED,
            symbols=["create_jwt", "verify_jwt"],
        )
        restored = FileSpec.from_dict(original.to_dict())
        assert restored.path == "auth/service.py"
        assert restored.status == FileStatus.GENERATED
        assert len(restored.symbols) == 2


class TestDomainSpec:
    def test_default(self) -> None:
        d = DomainSpec()
        assert d.name == ""
        assert d.files == []

    def test_roundtrip(self) -> None:
        original = DomainSpec(
            name="backend",
            description="Backend domain",
            files=["routes.py", "models.py"],
        )
        restored = DomainSpec.from_dict(original.to_dict())
        assert restored.name == "backend"
        assert len(restored.files) == 2


class TestProjectSpec:
    def test_default(self) -> None:
        spec = ProjectSpec()
        assert spec.id
        assert spec.status == ProjectStatus.PLANNING
        assert spec.file_count == 0

    def test_add_file(self) -> None:
        spec = ProjectSpec()
        spec.add_file(FileSpec(path="main.py", domain="backend"))
        assert spec.file_count == 1
        assert spec.get_file("main.py") is not None

    def test_add_file_updates_existing(self) -> None:
        spec = ProjectSpec()
        spec.add_file(FileSpec(path="main.py", description="v1"))
        spec.add_file(FileSpec(path="main.py", description="v2"))
        assert spec.file_count == 1
        assert spec.get_file("main.py").description == "v2"

    def test_get_file_not_found(self) -> None:
        spec = ProjectSpec()
        assert spec.get_file("nope.py") is None

    def test_add_domain(self) -> None:
        spec = ProjectSpec()
        spec.add_domain(DomainSpec(name="auth", description="Auth domain"))
        assert spec.domain_count == 1
        assert spec.get_domain("auth") is not None

    def test_add_domain_updates_existing(self) -> None:
        spec = ProjectSpec()
        spec.add_domain(DomainSpec(name="auth", description="v1"))
        spec.add_domain(DomainSpec(name="auth", description="v2"))
        assert spec.domain_count == 1
        assert spec.get_domain("auth").description == "v2"

    def test_calculate_progress(self) -> None:
        spec = ProjectSpec()
        spec.add_file(FileSpec(path="a.py", status=FileStatus.INTEGRATED))
        spec.add_file(FileSpec(path="b.py", status=FileStatus.PLANNED))
        spec.add_file(FileSpec(path="c.py", status=FileStatus.TESTED))
        spec.add_file(FileSpec(path="d.py", status=FileStatus.GENERATING))
        progress = spec.calculate_progress()
        assert progress == 0.5  # 2 of 4 are complete

    def test_roundtrip_dict(self) -> None:
        original = ProjectSpec(
            name="my-api",
            description="REST API",
            project_type="REST API",
            tech_stack=["FastAPI"],
            features=["Auth", "CRUD"],
            master_model="qwen2.5-coder:3b",
        )
        original.add_file(FileSpec(path="main.py"))
        original.add_domain(DomainSpec(name="backend"))

        restored = ProjectSpec.from_dict(original.to_dict())
        assert restored.name == "my-api"
        assert restored.file_count == 1
        assert restored.domain_count == 1
        assert restored.master_model == "qwen2.5-coder:3b"

    def test_yaml_roundtrip(self) -> None:
        original = ProjectSpec(
            name="yaml-test",
            tech_stack=["Python", "FastAPI"],
        )
        original.add_file(FileSpec(path="app.py", domain="backend"))

        yaml_str = original.to_yaml()
        assert "yaml-test" in yaml_str
        assert "FastAPI" in yaml_str

        restored = ProjectSpec.from_yaml(yaml_str)
        assert restored.name == "yaml-test"
        assert restored.file_count == 1

    def test_empty_progress(self) -> None:
        spec = ProjectSpec()
        assert spec.calculate_progress() == 0.0


class TestProjectStatus:
    def test_all_statuses(self) -> None:
        assert len(ProjectStatus) == 7

    def test_file_statuses(self) -> None:
        assert len(FileStatus) == 6
