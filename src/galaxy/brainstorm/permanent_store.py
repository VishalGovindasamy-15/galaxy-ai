"""Permanent ideas store — approved specification memory.

Stores ideas that the user has approved during brainstorming.
These become the source of truth for project creation.
Persisted to `.galaxy/brainstorm/permanent_ideas.yaml`.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from galaxy.brainstorm.types import Idea, IdeaCategory, IdeaStatus

logger = logging.getLogger(__name__)


class PermanentIdeaStore:
    """Store for approved/permanent ideas — the project's design truth.

    Only APPROVED ideas should be in this store. They represent confirmed
    architecture, validated features, and committed design decisions.

    Usage:
        perm = PermanentIdeaStore(workspace=Path("."))
        perm.promote(idea)  # Move from temp to permanent
        spec = perm.to_spec()  # Get structured spec for project creation
    """

    def __init__(self, workspace: Path | None = None) -> None:
        self._ideas: dict[str, Idea] = {}
        self._workspace = workspace
        self._file_path = (
            workspace / ".galaxy" / "brainstorm" / "permanent_ideas.yaml"
            if workspace
            else None
        )

    @property
    def count(self) -> int:
        """Number of approved ideas."""
        return len(self._ideas)

    def promote(self, idea: Idea) -> Idea:
        """Promote an idea from temp to permanent.

        The idea's status is set to APPROVED and it's added to this store.

        Args:
            idea: The idea to promote.

        Returns:
            The promoted idea (same object, status updated).
        """
        idea.approve()
        self._ideas[idea.id] = idea
        logger.info("Promoted idea to permanent: %s (%s)", idea.title, idea.id)
        return idea

    def add(self, idea: Idea) -> Idea:
        """Add an already-approved idea directly.

        Args:
            idea: An idea (should already have APPROVED status).

        Returns:
            The added idea.
        """
        self._ideas[idea.id] = idea
        return idea

    def get(self, idea_id: str) -> Idea | None:
        """Get an idea by ID."""
        return self._ideas.get(idea_id)

    def remove(self, idea_id: str) -> Idea | None:
        """Remove an idea from permanent store (demote back).

        Returns:
            The removed idea, or None if not found.
        """
        idea = self._ideas.pop(idea_id, None)
        if idea:
            logger.info("Removed idea from permanent: %s (%s)", idea.title, idea.id)
        return idea

    def list_all(self) -> list[Idea]:
        """List all permanent ideas."""
        return list(self._ideas.values())

    def list_by_category(self, category: IdeaCategory) -> list[Idea]:
        """List permanent ideas filtered by category."""
        return [i for i in self._ideas.values() if i.category == category]

    def list_by_priority(self) -> list[Idea]:
        """List ideas sorted by priority (1=highest first, 0=unset last)."""
        return sorted(
            self._ideas.values(),
            key=lambda i: (i.priority == 0, i.priority),
        )

    def update(self, idea_id: str, **kwargs: Any) -> Idea | None:
        """Update fields on a permanent idea (runtime mutation).

        This enables updating the spec during project creation via chat.

        Args:
            idea_id: ID of the idea to update.
            **kwargs: Fields to update.

        Returns:
            The updated idea, or None if not found.
        """
        idea = self._ideas.get(idea_id)
        if not idea:
            return None

        for key, value in kwargs.items():
            if hasattr(idea, key):
                setattr(idea, key, value)

        from datetime import datetime, timezone
        idea.updated_at = datetime.now(timezone.utc)
        return idea

    def to_spec(self) -> dict[str, Any]:
        """Convert permanent ideas to a structured project spec.

        This is what feeds into the Master agent for project creation.

        Returns:
            Dictionary with categorized ideas, constraints, and features.
        """
        spec: dict[str, Any] = {
            "features": [],
            "architecture": [],
            "constraints": [],
            "dependencies": [],
            "security": [],
            "workflows": [],
        }

        category_to_key = {
            IdeaCategory.FEATURE: "features",
            IdeaCategory.ARCHITECTURE: "architecture",
            IdeaCategory.CONSTRAINT: "constraints",
            IdeaCategory.DEPENDENCY: "dependencies",
            IdeaCategory.SECURITY: "security",
            IdeaCategory.WORKFLOW: "workflows",
        }

        for idea in self.list_by_priority():
            key = category_to_key.get(idea.category, "features")
            spec[key].append({
                "id": idea.id,
                "title": idea.title,
                "description": idea.description,
                "priority": idea.priority,
                "tags": idea.tags,
            })

        return spec

    def save(self) -> Path | None:
        """Persist permanent ideas to disk as YAML."""
        if not self._file_path:
            return None

        self._file_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": 1,
            "ideas": [idea.to_dict() for idea in self._ideas.values()],
        }

        with open(self._file_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        logger.debug("Saved %d permanent ideas to %s", len(self._ideas), self._file_path)
        return self._file_path

    def load(self) -> int:
        """Load permanent ideas from disk.

        Returns:
            Number of ideas loaded.
        """
        if not self._file_path or not self._file_path.exists():
            return 0

        with open(self._file_path) as f:
            data = yaml.safe_load(f)

        if not data or "ideas" not in data:
            return 0

        self._ideas.clear()
        for idea_data in data["ideas"]:
            idea = Idea.from_dict(idea_data)
            self._ideas[idea.id] = idea

        logger.debug("Loaded %d permanent ideas from %s", len(self._ideas), self._file_path)
        return len(self._ideas)

    def search(self, query: str) -> list[Idea]:
        """Search permanent ideas by title or description."""
        query_lower = query.lower()
        return [
            idea for idea in self._ideas.values()
            if query_lower in idea.title.lower()
            or query_lower in idea.description.lower()
        ]
