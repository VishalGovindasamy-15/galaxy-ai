"""5-level escalation manager.

Handles failures through an escalation chain:
Level 1: Worker retry with error context
Level 2: Domain agent restructures task
Level 3: Master agent re-plans
Level 4: Model fallback (switch to stronger model)
Level 5: Pause and ask user
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from galaxy.core.constants import (
    ESCALATION_LEVEL_DOMAIN,
    ESCALATION_LEVEL_MASTER,
    ESCALATION_LEVEL_MODEL_FALLBACK,
    ESCALATION_LEVEL_USER,
    ESCALATION_LEVEL_WORKER_RETRY,
    MAX_RETRY_LOOPS,
)
from galaxy.core.exceptions import MaxEscalationReachedError
from galaxy.core.types import EscalationLevel
from galaxy.events import Event
from galaxy.events.bus import EventBus

logger = logging.getLogger(__name__)


@dataclass
class EscalationRecord:
    """Record of an escalation attempt."""

    task_id: str
    level: int
    error: str
    action: str
    resolved: bool = False


class EscalationManager:
    """Manages the 5-level escalation chain for task failures."""

    def __init__(self, event_bus: EventBus, max_retries: int = MAX_RETRY_LOOPS) -> None:
        self.event_bus = event_bus
        self.max_retries = max_retries
        self._retry_counts: dict[str, int] = {}  # task_id → retry count
        self._history: list[EscalationRecord] = []

    async def handle_failure(
        self, task_id: str, error: str, current_level: int = 0,
    ) -> EscalationRecord:
        """Handle a task failure by escalating to the next level.

        Args:
            task_id: ID of the failed task.
            error: Error message.
            current_level: Current escalation level (0 = first failure).

        Returns:
            EscalationRecord describing the action taken.

        Raises:
            MaxEscalationReachedError: If all levels exhausted.
        """
        next_level = current_level + 1
        retries = self._retry_counts.get(task_id, 0)

        # Level 1: Worker retry
        if next_level == ESCALATION_LEVEL_WORKER_RETRY and retries < self.max_retries:
            self._retry_counts[task_id] = retries + 1
            record = EscalationRecord(
                task_id=task_id, level=1, error=error,
                action=f"Worker retry #{retries + 1} with error context",
            )
            await self._emit(record)
            self._history.append(record)
            return record

        # Level 2: Domain intervention
        if next_level <= ESCALATION_LEVEL_DOMAIN:
            record = EscalationRecord(
                task_id=task_id, level=2, error=error,
                action="Domain agent restructuring task",
            )
            await self._emit(record)
            self._history.append(record)
            return record

        # Level 3: Master restructure
        if next_level <= ESCALATION_LEVEL_MASTER:
            record = EscalationRecord(
                task_id=task_id, level=3, error=error,
                action="Master agent re-planning approach",
            )
            await self._emit(record)
            self._history.append(record)
            return record

        # Level 4: Model fallback
        if next_level <= ESCALATION_LEVEL_MODEL_FALLBACK:
            record = EscalationRecord(
                task_id=task_id, level=4, error=error,
                action="Switching to more capable model",
            )
            await self._emit(record)
            self._history.append(record)
            return record

        # Level 5: User intervention
        if next_level <= ESCALATION_LEVEL_USER:
            record = EscalationRecord(
                task_id=task_id, level=5, error=error,
                action="Pausing — requesting user intervention",
            )
            await self._emit(record)
            self._history.append(record)
            return record

        raise MaxEscalationReachedError(
            f"All escalation levels exhausted for task '{task_id}': {error}"
        )

    def get_retry_count(self, task_id: str) -> int:
        return self._retry_counts.get(task_id, 0)

    def reset_retries(self, task_id: str) -> None:
        self._retry_counts.pop(task_id, None)

    @property
    def history(self) -> list[EscalationRecord]:
        return list(self._history)

    async def _emit(self, record: EscalationRecord) -> None:
        await self.event_bus.publish(Event(
            type=f"escalation.level{record.level}",
            payload={
                "task_id": record.task_id,
                "level": record.level,
                "error": record.error,
                "action": record.action,
            },
        ))
