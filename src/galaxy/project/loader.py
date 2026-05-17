"""Project loader — save/load ProjectSpec to `.galaxy/project.yaml`.

Provides persistence for the project source-of-truth, enabling
projects to be portable, resumable, and rebuildable.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from galaxy.project.spec import ProjectSpec

logger = logging.getLogger(__name__)

DEFAULT_PROJECT_FILE = ".galaxy/project.yaml"


class ProjectLoader:
    """Loads and saves ProjectSpec to the filesystem.

    Usage:
        loader = ProjectLoader(workspace=Path("."))
        spec = loader.load()  # Load existing
        spec.name = "my-api"
        loader.save(spec)  # Persist
    """

    def __init__(self, workspace: Path | None = None) -> None:
        self._workspace = workspace
        self._file_path = (
            workspace / DEFAULT_PROJECT_FILE if workspace else None
        )

    @property
    def file_path(self) -> Path | None:
        return self._file_path

    @property
    def exists(self) -> bool:
        return self._file_path is not None and self._file_path.exists()

    def save(self, spec: ProjectSpec) -> Path | None:
        """Save a ProjectSpec to disk.

        Args:
            spec: The project specification to save.

        Returns:
            Path to saved file, or None if no workspace.
        """
        if not self._file_path:
            return None

        self._file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self._file_path, "w") as f:
            yaml.dump(
                spec.to_dict(),
                f,
                default_flow_style=False,
                sort_keys=False,
            )

        logger.info("Saved project spec to %s", self._file_path)
        return self._file_path

    def load(self) -> ProjectSpec | None:
        """Load a ProjectSpec from disk.

        Returns:
            The loaded ProjectSpec, or None if file doesn't exist.
        """
        if not self._file_path or not self._file_path.exists():
            return None

        with open(self._file_path) as f:
            data = yaml.safe_load(f)

        if not data:
            return ProjectSpec()

        spec = ProjectSpec.from_dict(data)
        logger.info("Loaded project spec: %s (%s)", spec.name, spec.id)
        return spec

    def load_or_create(self, name: str = "", description: str = "") -> ProjectSpec:
        """Load existing spec or create a new one.

        Args:
            name: Default name for new project.
            description: Default description for new project.

        Returns:
            Existing or newly created ProjectSpec.
        """
        existing = self.load()
        if existing:
            return existing

        spec = ProjectSpec(name=name, description=description)
        self.save(spec)
        return spec

    def delete(self) -> bool:
        """Delete the project spec file.

        Returns:
            True if deleted, False if not found.
        """
        if not self._file_path or not self._file_path.exists():
            return False
        self._file_path.unlink()
        return True
