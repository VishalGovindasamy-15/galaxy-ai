"""Project analyzer — analyzes existing projects to build a spec.

Scans the workspace to detect project structure, tech stack,
patterns, and creates a ProjectSpec from what it finds.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from galaxy.project.spec import DomainSpec, FileSpec, FileStatus, ProjectSpec

logger = logging.getLogger(__name__)

# File patterns for domain detection
DOMAIN_FILE_PATTERNS: dict[str, list[str]] = {
    "auth": ["auth", "login", "jwt", "session", "permission"],
    "database": ["model", "schema", "migration", "database", "orm"],
    "backend": ["route", "endpoint", "api", "controller", "service", "handler"],
    "frontend": ["component", "page", "view", "layout", "style"],
    "testing": ["test_", "spec_", "conftest", "_test"],
    "devops": ["docker", "ci", "deploy", "k8s", "terraform"],
    "config": ["config", "settings", "env", "constants"],
}

# Tech stack detection from files
TECH_DETECTORS: dict[str, dict[str, str]] = {
    "requirements.txt": {"file": "requirements.txt", "tech": "Python"},
    "pyproject.toml": {"file": "pyproject.toml", "tech": "Python"},
    "package.json": {"file": "package.json", "tech": "Node.js"},
    "Cargo.toml": {"file": "Cargo.toml", "tech": "Rust"},
    "go.mod": {"file": "go.mod", "tech": "Go"},
    "Dockerfile": {"file": "Dockerfile", "tech": "Docker"},
    "docker-compose.yml": {"file": "docker-compose.yml", "tech": "Docker Compose"},
}

SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", "dist", "build", ".galaxy",
    ".eggs", "*.egg-info",
}


class ProjectAnalyzer:
    """Analyzes an existing workspace to build a ProjectSpec.

    Usage:
        analyzer = ProjectAnalyzer(workspace=Path("."))
        spec = analyzer.analyze()
    """

    def __init__(self, workspace: Path) -> None:
        self._workspace = workspace

    def analyze(self, name: str = "") -> ProjectSpec:
        """Analyze the workspace and build a ProjectSpec.

        Args:
            name: Optional project name (defaults to directory name).

        Returns:
            ProjectSpec derived from workspace analysis.
        """
        spec = ProjectSpec(
            name=name or self._workspace.name,
            description=f"Analyzed from {self._workspace}",
        )

        # Detect tech stack
        spec.tech_stack = self._detect_tech_stack()

        # Scan files
        file_specs = self._scan_files()
        for fs in file_specs:
            spec.add_file(fs)

        # Build domains from files
        spec.domains = self._build_domains(file_specs)

        # Detect project type
        spec.project_type = self._detect_project_type(spec)

        # Calculate progress
        spec.calculate_progress()

        logger.info(
            "Analyzed workspace: %d files, %d domains, tech=%s",
            spec.file_count, spec.domain_count, spec.tech_stack,
        )
        return spec

    def _detect_tech_stack(self) -> list[str]:
        """Detect tech stack from project files."""
        stack: set[str] = set()

        for filename, info in TECH_DETECTORS.items():
            if (self._workspace / filename).exists():
                stack.add(info["tech"])

        # Check for specific imports in Python files
        try:
            for py_file in list(self._workspace.rglob("*.py"))[:20]:
                if self._should_skip(py_file):
                    continue
                try:
                    content = py_file.read_text()[:1000]
                    if "fastapi" in content.lower():
                        stack.add("FastAPI")
                    if "django" in content.lower():
                        stack.add("Django")
                    if "flask" in content.lower():
                        stack.add("Flask")
                    if "sqlalchemy" in content.lower():
                        stack.add("SQLAlchemy")
                except (OSError, UnicodeDecodeError):
                    continue
        except OSError:
            pass

        return sorted(stack) if stack else ["Unknown"]

    def _scan_files(self) -> list[FileSpec]:
        """Scan workspace for project files."""
        files: list[FileSpec] = []
        extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go"}

        try:
            for path in self._workspace.rglob("*"):
                if not path.is_file() or path.suffix not in extensions:
                    continue
                if self._should_skip(path):
                    continue

                relative = str(path.relative_to(self._workspace))
                domain = self._classify_domain(relative)
                symbols = self._extract_symbols(path)

                files.append(FileSpec(
                    path=relative,
                    description=f"Existing file in {domain} domain",
                    domain=domain,
                    status=FileStatus.INTEGRATED,  # Already exists
                    symbols=symbols,
                ))
        except OSError:
            pass

        return sorted(files, key=lambda f: f.path)[:100]  # Cap

    def _classify_domain(self, path: str) -> str:
        """Classify a file path into a domain."""
        path_lower = path.lower()
        for domain, patterns in DOMAIN_FILE_PATTERNS.items():
            if any(p in path_lower for p in patterns):
                return domain
        return "backend"  # Default

    def _extract_symbols(self, path: Path) -> list[str]:
        """Extract function and class names from a file."""
        symbols = []
        try:
            content = path.read_text()[:5000]
            symbols.extend(re.findall(r"^(?:async\s+)?def\s+(\w+)", content, re.MULTILINE))
            symbols.extend(re.findall(r"^class\s+(\w+)", content, re.MULTILINE))
        except (OSError, UnicodeDecodeError):
            pass
        return symbols[:20]  # Cap

    def _build_domains(self, files: list[FileSpec]) -> list[DomainSpec]:
        """Build domain specs from analyzed files."""
        domain_files: dict[str, list[str]] = {}
        for f in files:
            domain_files.setdefault(f.domain, []).append(f.path)

        return [
            DomainSpec(
                name=domain,
                description=f"{len(paths)} files in {domain} domain",
                files=paths,
            )
            for domain, paths in sorted(domain_files.items())
        ]

    def _detect_project_type(self, spec: ProjectSpec) -> str:
        """Detect project type from tech stack and files."""
        techs = " ".join(spec.tech_stack).lower()
        if "fastapi" in techs:
            return "REST API"
        if "django" in techs:
            return "Django Application"
        if "flask" in techs:
            return "Flask Application"
        if "react" in techs or "node" in techs:
            return "Web Application"
        if "rust" in techs:
            return "Rust Application"
        return "Python Application"

    def _should_skip(self, path: Path) -> bool:
        """Check if a path should be skipped."""
        return any(skip in path.parts for skip in SKIP_DIRS)
