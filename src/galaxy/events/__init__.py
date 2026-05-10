"""Galaxy event system — data models.

All events that flow through the Galaxy event bus are defined here.
Events are immutable dataclasses with a type string and payload.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_event_id() -> str:
    return uuid.uuid4().hex[:16]


@dataclass(frozen=True)
class Event:
    """An immutable event that flows through the event bus.

    Attributes:
        type: Dot-separated event type string (e.g. 'agent.task.completed').
        payload: Arbitrary data associated with the event.
        source: ID of the component that emitted the event.
        event_id: Unique event identifier.
        timestamp: UTC timestamp when the event was created.
    """

    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    event_id: str = field(default_factory=_new_event_id)
    timestamp: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Serialize event to dictionary."""
        return {
            "type": self.type,
            "payload": self.payload,
            "source": self.source,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Event:
        """Deserialize event from dictionary."""
        return cls(
            type=data["type"],
            payload=data.get("payload", {}),
            source=data.get("source", ""),
            event_id=data.get("event_id", _new_event_id()),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data
                else _utc_now()
            ),
        )


# ─── Standard Event Types ───────────────────────────────────────────────────

# Kernel lifecycle
GALAXY_BOOTING = "galaxy.booting"
GALAXY_BOOTED = "galaxy.booted"
GALAXY_SHUTTING_DOWN = "galaxy.shutting_down"
GALAXY_SHUTDOWN = "galaxy.shutdown"

# Agent lifecycle
AGENT_SPAWNED = "agent.spawned"
AGENT_TASK_STARTED = "agent.task.started"
AGENT_TASK_COMPLETED = "agent.task.completed"
AGENT_TASK_FAILED = "agent.task.failed"
AGENT_TERMINATED = "agent.terminated"

# Orchestrator
TASK_CREATED = "task.created"
TASK_QUEUED = "task.queued"
TASK_STARTED = "task.started"
TASK_COMPLETED = "task.completed"
TASK_FAILED = "task.failed"
TASK_RETRYING = "task.retrying"

# Escalation
ESCALATION_TRIGGERED = "escalation.triggered"
ESCALATION_RESOLVED = "escalation.resolved"

# Validation
VALIDATION_STARTED = "validation.started"
VALIDATION_STEP_PASSED = "validation.step.passed"
VALIDATION_STEP_FAILED = "validation.step.failed"
VALIDATION_COMPLETED = "validation.completed"

# Vault
CHECKPOINT_CREATED = "vault.checkpoint.created"
CHECKPOINT_LOADED = "vault.checkpoint.loaded"
CRASH_DETECTED = "vault.crash.detected"
RECOVERY_STARTED = "vault.recovery.started"
RECOVERY_COMPLETED = "vault.recovery.completed"

# User requests (from keyboard/UI)
PAUSE_REQUESTED = "galaxy.pause_requested"
RESUME_REQUESTED = "galaxy.resume_requested"
QUIT_REQUESTED = "galaxy.quit_requested"
CHECKPOINT_REQUESTED = "galaxy.checkpoint_requested"

# Model
MODEL_LOADED = "model.loaded"
MODEL_UNLOADED = "model.unloaded"
MODEL_FALLBACK_TRIGGERED = "model.fallback.triggered"

# Studio
STUDIO_STARTED = "studio.started"
STUDIO_CLIENT_CONNECTED = "studio.client.connected"
