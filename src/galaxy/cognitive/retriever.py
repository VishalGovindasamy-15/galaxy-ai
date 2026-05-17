"""Context Retriever — gathers relevant context for planning.

Stage 3 of the cognitive pipeline. Retrieves relevant files, code patterns,
documentation, and memory from the workspace and project context.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from galaxy.cognitive.types import (
    PipelineStage,
    RetrievedContext,
    StageResult,
)

logger = logging.getLogger(__name__)

# Common project patterns to detect
PATTERN_INDICATORS: dict[str, list[str]] = {
    "FastAPI project": ["main.py", "app.py", "routers/", "requirements.txt"],
    "Django project": ["manage.py", "settings.py", "urls.py"],
    "Flask project": ["app.py", "flask", "blueprints/"],
    "React project": ["package.json", "src/App.tsx", "src/App.jsx"],
    "Python package": ["setup.py", "pyproject.toml", "src/"],
    "Docker project": ["Dockerfile", "docker-compose.yml"],
    "Monorepo": ["packages/", "apps/", "workspace"],
}


class ContextRetriever:
    """Retrieves relevant context from workspace and memory.

    Scans the project workspace for existing code, patterns,
    and conventions to inform the planning stages.
    """

    def __init__(self, workspace: Path | None = None) -> None:
        self._workspace = workspace

    def retrieve(
        self,
        prompt: str = "",
        domains: list[str] | None = None,
        tech_stack: list[str] | None = None,
    ) -> RetrievedContext:
        """Retrieve context relevant to the current task.

        Args:
            prompt: The project prompt for context matching.
            domains: Active domains to focus on.
            tech_stack: Technologies to look for.

        Returns:
            RetrievedContext with gathered information.
        """
        ctx = RetrievedContext()

        if self._workspace and self._workspace.exists():
            ctx.relevant_files = self._scan_workspace()
            ctx.patterns = self._detect_patterns()
            ctx.code_snippets = self._extract_snippets(domains or [])

        # Add documentation hints based on tech stack
        if tech_stack:
            ctx.documentation = self._get_tech_docs(tech_stack)

        return ctx

    def retrieve_to_stage_result(
        self,
        prompt: str = "",
        domains: list[str] | None = None,
        tech_stack: list[str] | None = None,
    ) -> StageResult:
        """Retrieve context and wrap in a StageResult."""
        start = time.monotonic()
        ctx = self.retrieve(prompt, domains, tech_stack)
        duration = (time.monotonic() - start) * 1000

        result = StageResult(
            stage=PipelineStage.RETRIEVE,
            input_data=prompt,
            metadata={
                "files_found": len(ctx.relevant_files),
                "patterns": ctx.patterns,
                "snippets_count": len(ctx.code_snippets),
            },
        )
        result.complete(ctx.to_prompt(), duration)
        return result

    def _scan_workspace(self) -> list[str]:
        """Scan workspace for relevant files."""
        if not self._workspace:
            return []

        relevant = []
        extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".yaml", ".yml", ".toml", ".json", ".md"}

        try:
            for path in self._workspace.rglob("*"):
                if path.is_file() and path.suffix in extensions:
                    # Skip common non-relevant dirs
                    parts = path.parts
                    if any(skip in parts for skip in (
                        ".git", "__pycache__", "node_modules", ".venv",
                        "venv", ".mypy_cache", ".pytest_cache", "dist", "build",
                    )):
                        continue
                    relative = str(path.relative_to(self._workspace))
                    relevant.append(relative)
        except (PermissionError, OSError):
            pass

        return sorted(relevant)[:50]  # Cap at 50 files

    def _detect_patterns(self) -> list[str]:
        """Detect project patterns from file structure."""
        if not self._workspace:
            return []

        detected = []
        for pattern_name, indicators in PATTERN_INDICATORS.items():
            matches = 0
            for indicator in indicators:
                check_path = self._workspace / indicator
                if check_path.exists():
                    matches += 1
            if matches >= 2:
                detected.append(pattern_name)
            elif matches >= 1:
                detected.append(f"Possible {pattern_name}")

        return detected

    def _extract_snippets(self, domains: list[str]) -> list[str]:
        """Extract relevant code snippets from existing files."""
        if not self._workspace:
            return []

        snippets = []
        # Look for key files
        key_files = ["main.py", "app.py", "config.py", "models.py"]

        for filename in key_files:
            for path in self._workspace.rglob(filename):
                try:
                    content = path.read_text()
                    if len(content) < 5000:  # Don't load huge files
                        snippets.append(f"# {path.relative_to(self._workspace)}\n{content[:500]}")
                except (PermissionError, OSError, UnicodeDecodeError):
                    continue

        return snippets[:5]  # Cap at 5 snippets

    def _get_tech_docs(self, tech_stack: list[str]) -> list[str]:
        """Get documentation hints for the tech stack."""
        docs = []
        tech_hints = {
            "FastAPI": "FastAPI uses async def routes, Pydantic models, and dependency injection",
            "React": "React uses functional components with hooks (useState, useEffect)",
            "PostgreSQL": "Use SQLAlchemy ORM or asyncpg for PostgreSQL connections",
            "JWT": "Use python-jose or PyJWT for JWT token handling",
            "Docker": "Use multi-stage builds for production Docker images",
            "pytest": "Use fixtures, parametrize, and conftest.py for test organization",
            "SQLAlchemy": "Use declarative models with async session for SQLAlchemy 2.0",
            "Redis": "Use aioredis for async Redis connections",
            "Pydantic": "Pydantic v2 uses model_validate() instead of parse_obj()",
        }
        for tech in tech_stack:
            for key, hint in tech_hints.items():
                if key.lower() in tech.lower():
                    docs.append(hint)
        return docs
