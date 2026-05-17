"""Project specification — the single source of truth.

Defines the ProjectSpec that lives in `.galaxy/project.yaml`.
This is the portable, human-readable specification that captures
everything about a project: its structure, features, configuration,
and build state.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import yaml


class ProjectStatus(str, Enum):
    """Status of the overall project."""
    PLANNING = "planning"
    BRAINSTORMING = "brainstorming"
    BUILDING = "building"
    TESTING = "testing"
    AUDITING = "auditing"
    COMPLETE = "complete"
    PAUSED = "paused"


class FileStatus(str, Enum):
    """Status of a file in the project."""
    PLANNED = "planned"
    GENERATING = "generating"
    GENERATED = "generated"
    INTEGRATED = "integrated"
    TESTED = "tested"
    AUDITED = "audited"


@dataclass
class FileSpec:
    """Specification for a single file in the project."""
    path: str = ""
    description: str = ""
    domain: str = ""
    status: FileStatus = FileStatus.PLANNED
    symbols: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    chunk_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "description": self.description,
            "domain": self.domain,
            "status": self.status.value,
            "symbols": self.symbols,
            "dependencies": self.dependencies,
            "chunk_ids": self.chunk_ids,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FileSpec:
        return cls(
            path=data.get("path", ""),
            description=data.get("description", ""),
            domain=data.get("domain", ""),
            status=FileStatus(data.get("status", "planned")),
            symbols=data.get("symbols", []),
            dependencies=data.get("dependencies", []),
            chunk_ids=data.get("chunk_ids", []),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if "created_at" in data
                else datetime.now(timezone.utc)
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if "updated_at" in data
                else datetime.now(timezone.utc)
            ),
        )


@dataclass
class DomainSpec:
    """Specification for a domain in the project."""
    name: str = ""
    description: str = ""
    model: str = ""
    files: list[str] = field(default_factory=list)  # File paths belonging to this domain

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "model": self.model,
            "files": self.files,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DomainSpec:
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            model=data.get("model", ""),
            files=data.get("files", []),
        )


@dataclass
class ProjectSpec:
    """Complete project specification — the source of truth.

    Stored in `.galaxy/project.yaml`. Contains everything needed
    to understand, rebuild, and continue a project.
    """
    # Identity
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    description: str = ""
    version: str = "1.0.0"

    # Status
    status: ProjectStatus = ProjectStatus.PLANNING
    progress: float = 0.0  # 0.0 to 1.0

    # Technical
    project_type: str = ""
    tech_stack: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    # Structure
    files: list[FileSpec] = field(default_factory=list)
    domains: list[DomainSpec] = field(default_factory=list)

    # Models
    master_model: str = ""
    domain_model: str = ""
    worker_model: str = ""

    # Config
    config: dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def domain_count(self) -> int:
        return len(self.domains)

    def get_file(self, path: str) -> FileSpec | None:
        for f in self.files:
            if f.path == path:
                return f
        return None

    def add_file(self, file_spec: FileSpec) -> None:
        existing = self.get_file(file_spec.path)
        if existing:
            # Update existing
            idx = self.files.index(existing)
            self.files[idx] = file_spec
        else:
            self.files.append(file_spec)
        self.updated_at = datetime.now(timezone.utc)

    def get_domain(self, name: str) -> DomainSpec | None:
        for d in self.domains:
            if d.name == name:
                return d
        return None

    def add_domain(self, domain_spec: DomainSpec) -> None:
        existing = self.get_domain(domain_spec.name)
        if existing:
            idx = self.domains.index(existing)
            self.domains[idx] = domain_spec
        else:
            self.domains.append(domain_spec)
        self.updated_at = datetime.now(timezone.utc)

    def calculate_progress(self) -> float:
        if not self.files:
            return 0.0
        completed = sum(1 for f in self.files if f.status in (
            FileStatus.INTEGRATED, FileStatus.TESTED, FileStatus.AUDITED
        ))
        self.progress = completed / len(self.files)
        return self.progress

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "status": self.status.value,
            "progress": self.progress,
            "project_type": self.project_type,
            "tech_stack": self.tech_stack,
            "features": self.features,
            "constraints": self.constraints,
            "files": [f.to_dict() for f in self.files],
            "domains": [d.to_dict() for d in self.domains],
            "master_model": self.master_model,
            "domain_model": self.domain_model,
            "worker_model": self.worker_model,
            "config": self.config,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectSpec:
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            status=ProjectStatus(data.get("status", "planning")),
            progress=data.get("progress", 0.0),
            project_type=data.get("project_type", ""),
            tech_stack=data.get("tech_stack", []),
            features=data.get("features", []),
            constraints=data.get("constraints", []),
            files=[FileSpec.from_dict(f) for f in data.get("files", [])],
            domains=[DomainSpec.from_dict(d) for d in data.get("domains", [])],
            master_model=data.get("master_model", ""),
            domain_model=data.get("domain_model", ""),
            worker_model=data.get("worker_model", ""),
            config=data.get("config", {}),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if "created_at" in data
                else datetime.now(timezone.utc)
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if "updated_at" in data
                else datetime.now(timezone.utc)
            ),
        )

    def to_yaml(self) -> str:
        """Serialize to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> ProjectSpec:
        """Deserialize from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data or {})
