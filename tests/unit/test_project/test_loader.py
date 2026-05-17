"""Tests for galaxy.project.loader."""

from pathlib import Path

from galaxy.project.loader import ProjectLoader
from galaxy.project.spec import FileSpec, ProjectSpec


class TestProjectLoader:
    def test_no_workspace(self) -> None:
        loader = ProjectLoader()
        assert not loader.exists
        assert loader.load() is None
        assert loader.save(ProjectSpec()) is None

    def test_save_and_load(self, tmp_path: Path) -> None:
        loader = ProjectLoader(workspace=tmp_path)
        spec = ProjectSpec(name="test-project", description="A test")
        spec.add_file(FileSpec(path="main.py", domain="backend"))

        saved_path = loader.save(spec)
        assert saved_path is not None
        assert saved_path.exists()

        loaded = loader.load()
        assert loaded is not None
        assert loaded.name == "test-project"
        assert loaded.file_count == 1

    def test_load_nonexistent(self, tmp_path: Path) -> None:
        loader = ProjectLoader(workspace=tmp_path)
        assert loader.load() is None

    def test_load_or_create_new(self, tmp_path: Path) -> None:
        loader = ProjectLoader(workspace=tmp_path)
        spec = loader.load_or_create(name="new-project")
        assert spec.name == "new-project"
        assert loader.exists

    def test_load_or_create_existing(self, tmp_path: Path) -> None:
        loader = ProjectLoader(workspace=tmp_path)
        original = ProjectSpec(name="existing")
        loader.save(original)

        loaded = loader.load_or_create(name="should-not-use")
        assert loaded.name == "existing"

    def test_delete(self, tmp_path: Path) -> None:
        loader = ProjectLoader(workspace=tmp_path)
        loader.save(ProjectSpec(name="temp"))
        assert loader.exists

        assert loader.delete() is True
        assert not loader.exists

    def test_delete_nonexistent(self, tmp_path: Path) -> None:
        loader = ProjectLoader(workspace=tmp_path)
        assert loader.delete() is False

    def test_file_path(self, tmp_path: Path) -> None:
        loader = ProjectLoader(workspace=tmp_path)
        assert loader.file_path is not None
        assert ".galaxy/project.yaml" in str(loader.file_path)
