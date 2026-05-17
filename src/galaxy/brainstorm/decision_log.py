"""Decision log — audit trail for brainstorming sessions.

Records every decision made during brainstorming with timestamps,
reasons, and context. Answers: "why was this chosen? when? by whom?"
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from galaxy.brainstorm.types import DecisionRecord, DecisionType

logger = logging.getLogger(__name__)


class DecisionLog:
    """Append-only log of decisions made during brainstorming.

    Every idea creation, approval, rejection, merge, and architectural
    decision is recorded with timestamps and reasoning for full traceability.

    Usage:
        log = DecisionLog(workspace=Path("."))
        log.record(DecisionType.IDEA_APPROVED, idea_id="abc", reason="Critical for MVP")
        history = log.query(idea_id="abc")
    """

    def __init__(self, workspace: Path | None = None) -> None:
        self._records: list[DecisionRecord] = []
        self._workspace = workspace
        self._file_path = (
            workspace / ".galaxy" / "brainstorm" / "decision_log.yaml"
            if workspace
            else None
        )

    @property
    def count(self) -> int:
        """Number of recorded decisions."""
        return len(self._records)

    def record(
        self,
        decision_type: DecisionType,
        idea_id: str | None = None,
        description: str = "",
        reason: str = "",
        context: dict[str, Any] | None = None,
    ) -> DecisionRecord:
        """Record a new decision.

        Args:
            decision_type: Type of decision being made.
            idea_id: Related idea ID (if applicable).
            description: What was decided.
            reason: Why it was decided.
            context: Additional context data.

        Returns:
            The created DecisionRecord.
        """
        record = DecisionRecord(
            decision_type=decision_type,
            idea_id=idea_id,
            description=description,
            reason=reason,
            context=context or {},
        )
        self._records.append(record)
        logger.debug(
            "Decision recorded: %s — %s",
            decision_type.value,
            description[:80] if description else "(no description)",
        )
        return record

    def query(
        self,
        idea_id: str | None = None,
        decision_type: DecisionType | None = None,
        limit: int | None = None,
    ) -> list[DecisionRecord]:
        """Query the decision log with optional filters.

        Args:
            idea_id: Filter by related idea ID.
            decision_type: Filter by decision type.
            limit: Maximum number of results (most recent first).

        Returns:
            List of matching decision records (newest first).
        """
        results = self._records.copy()

        if idea_id is not None:
            results = [r for r in results if r.idea_id == idea_id]

        if decision_type is not None:
            results = [r for r in results if r.decision_type == decision_type]

        # Newest first
        results.sort(key=lambda r: r.timestamp, reverse=True)

        if limit is not None:
            results = results[:limit]

        return results

    def list_all(self) -> list[DecisionRecord]:
        """List all decisions in chronological order."""
        return sorted(self._records, key=lambda r: r.timestamp)

    def get_idea_history(self, idea_id: str) -> list[DecisionRecord]:
        """Get the full history of decisions for a specific idea.

        Returns decisions in chronological order.
        """
        return sorted(
            [r for r in self._records if r.idea_id == idea_id],
            key=lambda r: r.timestamp,
        )

    def clear(self) -> int:
        """Clear all records. Returns count of cleared records."""
        count = len(self._records)
        self._records.clear()
        return count

    def save(self) -> Path | None:
        """Persist decision log to disk."""
        if not self._file_path:
            return None

        self._file_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": 1,
            "decisions": [r.to_dict() for r in self._records],
        }

        with open(self._file_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        logger.debug("Saved %d decisions to %s", len(self._records), self._file_path)
        return self._file_path

    def load(self) -> int:
        """Load decision log from disk.

        Returns:
            Number of records loaded.
        """
        if not self._file_path or not self._file_path.exists():
            return 0

        with open(self._file_path) as f:
            data = yaml.safe_load(f)

        if not data or "decisions" not in data:
            return 0

        self._records.clear()
        for record_data in data["decisions"]:
            record = DecisionRecord.from_dict(record_data)
            self._records.append(record)

        logger.debug("Loaded %d decisions from %s", len(self._records), self._file_path)
        return len(self._records)
