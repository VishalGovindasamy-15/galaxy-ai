"""Brainstorm engine — orchestrates the brainstorming session.

Coordinates temp store, permanent store, and decision log to provide
a complete brainstorming workflow: ideate → refine → evaluate → approve.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from galaxy.brainstorm.decision_log import DecisionLog
from galaxy.brainstorm.permanent_store import PermanentIdeaStore
from galaxy.brainstorm.temp_store import TempIdeaStore
from galaxy.brainstorm.types import (
    BrainstormMode,
    BrainstormPhase,
    BrainstormSession,
    BrainstormSummary,
    DecisionType,
    Idea,
    IdeaCategory,
    IdeaStatus,
)

logger = logging.getLogger(__name__)


class BrainstormEngine:
    """Orchestrates the full brainstorming lifecycle.

    Manages the flow between temp ideas (exploration) and permanent ideas
    (approved truth), with a full decision audit trail.

    Usage:
        engine = BrainstormEngine(workspace=Path("."))
        session = engine.start_session("Build a REST API", mode=BrainstormMode.STRUCTURED)
        idea = engine.add_idea("JWT Authentication", "Token-based auth with refresh")
        engine.approve_idea(idea.id)
        spec = engine.get_project_spec()
    """

    def __init__(self, workspace: Path | None = None) -> None:
        self._workspace = workspace
        self._temp_store = TempIdeaStore(workspace)
        self._permanent_store = PermanentIdeaStore(workspace)
        self._decision_log = DecisionLog(workspace)
        self._session: BrainstormSession | None = None

    @property
    def session(self) -> BrainstormSession | None:
        """Current brainstorming session."""
        return self._session

    @property
    def temp_store(self) -> TempIdeaStore:
        """Access to temp ideas store."""
        return self._temp_store

    @property
    def permanent_store(self) -> PermanentIdeaStore:
        """Access to permanent ideas store."""
        return self._permanent_store

    @property
    def decision_log(self) -> DecisionLog:
        """Access to decision log."""
        return self._decision_log

    def start_session(
        self,
        prompt: str = "",
        project_name: str = "",
        mode: BrainstormMode = BrainstormMode.STRUCTURED,
        config: dict[str, Any] | None = None,
    ) -> BrainstormSession:
        """Start a new brainstorming session.

        Args:
            prompt: Initial project prompt from the user.
            project_name: Name of the project being brainstormed.
            mode: Brainstorming mode (free_form, structured, guided).
            config: Session configuration overrides.

        Returns:
            The created BrainstormSession.
        """
        self._session = BrainstormSession(
            prompt=prompt,
            project_name=project_name,
            mode=mode,
            config=config or {},
        )

        self._decision_log.record(
            DecisionType.SESSION_STARTED,
            description=f"Brainstorming session started: {prompt[:100]}",
            context={"mode": mode.value, "project": project_name},
        )

        logger.info("Brainstorm session started: %s (mode=%s)", self._session.id, mode.value)
        return self._session

    def end_session(self) -> BrainstormSummary:
        """End the current brainstorming session and generate summary.

        Returns:
            Summary of the brainstorming session.
        """
        if not self._session:
            return BrainstormSummary()

        self._session.phase = BrainstormPhase.COMPLETE

        self._decision_log.record(
            DecisionType.SESSION_ENDED,
            description="Brainstorming session ended",
        )

        summary = self._generate_summary()

        # Auto-save
        self.save()

        logger.info(
            "Brainstorm session ended: %d ideas (%d approved)",
            summary.total_ideas,
            summary.approved_ideas,
        )
        return summary

    def add_idea(
        self,
        title: str,
        description: str = "",
        category: IdeaCategory = IdeaCategory.FEATURE,
        tags: list[str] | None = None,
        priority: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> Idea:
        """Add a new idea to the temp store (exploration).

        Args:
            title: Short title.
            description: Detailed description.
            category: Category classification.
            tags: Optional tags.
            priority: Priority level.
            metadata: Additional metadata.

        Returns:
            The created Idea.
        """
        idea = self._temp_store.add(
            title=title,
            description=description,
            category=category,
            tags=tags,
            priority=priority,
            metadata=metadata,
        )

        # Track in session
        if self._session:
            self._session.idea_ids.append(idea.id)

        # Log decision
        record = self._decision_log.record(
            DecisionType.IDEA_CREATED,
            idea_id=idea.id,
            description=f"Created idea: {title}",
            context={"category": category.value},
        )
        if self._session:
            self._session.decision_ids.append(record.id)

        return idea

    def approve_idea(self, idea_id: str, reason: str = "") -> Idea | None:
        """Approve an idea — move from temp to permanent.

        Args:
            idea_id: ID of the idea to approve.
            reason: Why it was approved.

        Returns:
            The approved Idea, or None if not found.
        """
        idea = self._temp_store.get(idea_id)
        if not idea:
            return None

        # Remove from temp, add to permanent
        self._temp_store.remove(idea_id)
        self._permanent_store.promote(idea)

        # Log decision
        record = self._decision_log.record(
            DecisionType.IDEA_APPROVED,
            idea_id=idea_id,
            description=f"Approved: {idea.title}",
            reason=reason,
        )
        if self._session:
            self._session.decision_ids.append(record.id)

        logger.info("Idea approved: %s (%s)", idea.title, idea_id)
        return idea

    def reject_idea(self, idea_id: str, reason: str = "") -> Idea | None:
        """Reject an idea — mark as rejected in temp store.

        Args:
            idea_id: ID of the idea to reject.
            reason: Why it was rejected.

        Returns:
            The rejected Idea, or None if not found.
        """
        idea = self._temp_store.get(idea_id)
        if not idea:
            return None

        idea.reject()

        record = self._decision_log.record(
            DecisionType.IDEA_REJECTED,
            idea_id=idea_id,
            description=f"Rejected: {idea.title}",
            reason=reason,
        )
        if self._session:
            self._session.decision_ids.append(record.id)

        logger.info("Idea rejected: %s (%s)", idea.title, idea_id)
        return idea

    def defer_idea(self, idea_id: str, reason: str = "") -> Idea | None:
        """Defer an idea for later consideration.

        Args:
            idea_id: ID of the idea to defer.
            reason: Why it was deferred.

        Returns:
            The deferred Idea, or None if not found.
        """
        idea = self._temp_store.get(idea_id)
        if not idea:
            return None

        idea.defer()

        record = self._decision_log.record(
            DecisionType.IDEA_DEFERRED,
            idea_id=idea_id,
            description=f"Deferred: {idea.title}",
            reason=reason,
        )
        if self._session:
            self._session.decision_ids.append(record.id)

        return idea

    def update_permanent_idea(self, idea_id: str, **kwargs: Any) -> Idea | None:
        """Update a permanent idea during project creation (runtime mutation).

        This enables modifying the approved spec while the project is being built.

        Args:
            idea_id: ID of the permanent idea to update.
            **kwargs: Fields to update.

        Returns:
            The updated Idea, or None if not found.
        """
        updated = self._permanent_store.update(idea_id, **kwargs)
        if updated:
            self._decision_log.record(
                DecisionType.IDEA_UPDATED,
                idea_id=idea_id,
                description=f"Updated permanent idea: {updated.title}",
                context={"updated_fields": list(kwargs.keys())},
            )
        return updated

    def advance_phase(self) -> BrainstormPhase | None:
        """Advance the session to the next phase.

        Returns:
            The new phase, or None if no session.
        """
        if not self._session:
            return None

        new_phase = self._session.advance_phase()

        self._decision_log.record(
            DecisionType.PHASE_CHANGED,
            description=f"Phase changed to: {new_phase.value}",
        )

        return new_phase

    def get_project_spec(self) -> dict[str, Any]:
        """Get the structured project spec from approved ideas.

        This is what feeds into the Master agent for project creation.

        Returns:
            Dictionary with categorized features, constraints, etc.
        """
        return self._permanent_store.to_spec()

    def save(self) -> None:
        """Persist all stores to disk."""
        self._temp_store.save()
        self._permanent_store.save()
        self._decision_log.save()

    def load(self) -> dict[str, int]:
        """Load all stores from disk.

        Returns:
            Dict with counts of loaded items per store.
        """
        return {
            "temp_ideas": self._temp_store.load(),
            "permanent_ideas": self._permanent_store.load(),
            "decisions": self._decision_log.load(),
        }

    def _generate_summary(self) -> BrainstormSummary:
        """Generate summary statistics for the current session."""
        all_temp = self._temp_store.list_all()
        all_perm = self._permanent_store.list_all()

        # Count categories
        categories: dict[str, int] = {}
        for idea in all_temp + all_perm:
            cat = idea.category.value
            categories[cat] = categories.get(cat, 0) + 1

        return BrainstormSummary(
            session_id=self._session.id if self._session else "",
            total_ideas=len(all_temp) + len(all_perm),
            approved_ideas=len(all_perm),
            rejected_ideas=len([i for i in all_temp if i.status == IdeaStatus.REJECTED]),
            deferred_ideas=len([i for i in all_temp if i.status == IdeaStatus.DEFERRED]),
            pending_ideas=len([i for i in all_temp if i.status.is_active()]),
            total_decisions=self._decision_log.count,
            categories=categories,
        )
