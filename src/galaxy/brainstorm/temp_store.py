"""Temp ideas store — working memory for brainstorming exploration.

Stores ideas that are being explored but not yet approved.
Ideas live here until the user promotes them to permanent or rejects them.
Persisted to `.galaxy/brainstorm/temp_ideas.yaml` for session resumability.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from galaxy.brainstorm.types import Idea, IdeaCategory, IdeaStatus

logger = logging.getLogger(__name__)


class TempIdeaStore:
    """In-memory + file-backed store for temporary (exploration) ideas.

    Ideas in the temp store are drafts being explored. They haven't been
    approved by the user yet. This is the "working memory" of brainstorming.

    Usage:
        store = TempIdeaStore(workspace=Path("."))
        idea = store.add("Add JWT auth", "Implement JWT-based authentication")
        store.save()  # Persist to disk
    """

    def __init__(self, workspace: Path | None = None) -> None:
        self._ideas: dict[str, Idea] = {}
        self._workspace = workspace
        self._file_path = (
            workspace / ".galaxy" / "brainstorm" / "temp_ideas.yaml"
            if workspace
            else None
        )

    @property
    def count(self) -> int:
        """Number of ideas in the store."""
        return len(self._ideas)

    def add(
        self,
        title: str,
        description: str = "",
        category: IdeaCategory = IdeaCategory.FEATURE,
        tags: list[str] | None = None,
        priority: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> Idea:
        """Add a new idea to the temp store.

        Args:
            title: Short title for the idea.
            description: Detailed description.
            category: Category classification.
            tags: Optional tags for filtering.
            priority: Priority level (0=unset, 1=highest).
            metadata: Additional metadata.

        Returns:
            The created Idea.
        """
        idea = Idea(
            title=title,
            description=description,
            category=category,
            tags=tags or [],
            priority=priority,
            metadata=metadata or {},
        )
        self._ideas[idea.id] = idea
        logger.debug("Added temp idea: %s (%s)", idea.title, idea.id)
        return idea

    def get(self, idea_id: str) -> Idea | None:
        """Get an idea by ID."""
        return self._ideas.get(idea_id)

    def remove(self, idea_id: str) -> Idea | None:
        """Remove an idea from the store.

        Returns:
            The removed Idea, or None if not found.
        """
        idea = self._ideas.pop(idea_id, None)
        if idea:
            logger.debug("Removed temp idea: %s (%s)", idea.title, idea.id)
        return idea

    def list_all(self) -> list[Idea]:
        """List all ideas in the store."""
        return list(self._ideas.values())

    def list_by_status(self, status: IdeaStatus) -> list[Idea]:
        """List ideas filtered by status."""
        return [i for i in self._ideas.values() if i.status == status]

    def list_by_category(self, category: IdeaCategory) -> list[Idea]:
        """List ideas filtered by category."""
        return [i for i in self._ideas.values() if i.category == category]

    def list_active(self) -> list[Idea]:
        """List ideas that are still being explored (DRAFT or EXPLORING)."""
        return [i for i in self._ideas.values() if i.status.is_active()]

    def update(self, idea_id: str, **kwargs: Any) -> Idea | None:
        """Update fields on an existing idea.

        Args:
            idea_id: ID of the idea to update.
            **kwargs: Fields to update (title, description, category, etc.)

        Returns:
            The updated Idea, or None if not found.
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

    def clear(self) -> int:
        """Remove all ideas. Returns the count of removed ideas."""
        count = len(self._ideas)
        self._ideas.clear()
        logger.debug("Cleared %d temp ideas", count)
        return count

    def save(self) -> Path | None:
        """Persist ideas to disk as YAML.

        Returns:
            Path to the saved file, or None if no workspace configured.
        """
        if not self._file_path:
            return None

        self._file_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": 1,
            "ideas": [idea.to_dict() for idea in self._ideas.values()],
        }

        with open(self._file_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        logger.debug("Saved %d temp ideas to %s", len(self._ideas), self._file_path)
        return self._file_path

    def load(self) -> int:
        """Load ideas from disk.

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

        logger.debug("Loaded %d temp ideas from %s", len(self._ideas), self._file_path)
        return len(self._ideas)

    def search(self, query: str) -> list[Idea]:
        """Search ideas by title or description (case-insensitive).

        Args:
            query: Search string.

        Returns:
            List of matching ideas.
        """
        query_lower = query.lower()
        return [
            idea for idea in self._ideas.values()
            if query_lower in idea.title.lower()
            or query_lower in idea.description.lower()
        ]
