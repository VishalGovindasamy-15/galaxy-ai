"""Galaxy shared type definitions.

All enums, dataclasses, and type aliases used across subsystems.
This module has ZERO internal dependencies (only stdlib + pydantic).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ─── Enums ───────────────────────────────────────────────────────────────────


class AgentTier(str, Enum):
    """Agent hierarchy tiers."""

    MASTER = "master"
    DOMAIN = "domain"
    WORKER = "worker"


class TaskStatus(str, Enum):
    """Lifecycle states for a task in the task graph."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    VALIDATING = "validating"
    RETRYING = "retrying"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

    def is_terminal(self) -> bool:
        """Return True if this status is a final state."""
        return self in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED)

    def is_active(self) -> bool:
        """Return True if this status means work is happening."""
        return self in (TaskStatus.RUNNING, TaskStatus.VALIDATING, TaskStatus.RETRYING)


class AgentStatus(str, Enum):
    """Agent lifecycle states."""

    IDLE = "idle"
    WORKING = "working"
    VALIDATING = "validating"
    RETRYING = "retrying"
    FAILED = "failed"
    QUEUED = "queued"
    TERMINATED = "terminated"


class EscalationLevel(int, Enum):
    """5-level escalation chain."""

    WORKER_RETRY = 1
    DOMAIN_INTERVENTION = 2
    MASTER_RESTRUCTURE = 3
    MODEL_FALLBACK = 4
    USER_INTERVENTION = 5


class SchedulerMode(str, Enum):
    """Scheduler optimization modes."""

    SPEED = "speed"
    BALANCED = "balanced"
    QUALITY = "quality"


class MemoryLevel(str, Enum):
    """5-level memory hierarchy."""

    GLOBAL = "global"
    PROJECT = "project"
    DOMAIN = "domain"
    AGENT = "agent"
    TASK = "task"


class TrustBand(str, Enum):
    """Trust score bands for auto-merge decisions."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    CRITICAL = "CRITICAL"


class ValidationStep(str, Enum):
    """Steps in the Forge validation pipeline."""

    SYNTAX = "syntax"
    IMPORTS = "imports"
    LINT = "lint"
    TYPE_CHECK = "type_check"
    BUILD = "build"
    TEST = "test"
    SECURITY = "security"
    DOC_COVERAGE = "doc_coverage"


# ─── Core Data Classes ──────────────────────────────────────────────────────


def _utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


def _new_id() -> str:
    """Generate a new unique ID."""
    return uuid.uuid4().hex[:12]


@dataclass
class Task:
    """A unit of work in the task graph."""

    id: str = field(default_factory=_new_id)
    description: str = ""
    file_path: str = ""
    domain: str = ""
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: str = ""
    dependencies: list[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    escalation_level: EscalationLevel = EscalationLevel.WORKER_RETRY
    created_at: datetime = field(default_factory=_utc_now)
    completed_at: datetime | None = None
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def mark_running(self, agent_id: str) -> None:
        """Transition task to running state."""
        self.status = TaskStatus.RUNNING
        self.assigned_agent = agent_id

    def mark_completed(self) -> None:
        """Transition task to completed state."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = _utc_now()

    def mark_failed(self, error: str) -> None:
        """Transition task to failed state."""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = _utc_now()

    def mark_retrying(self) -> None:
        """Increment retry count and set retrying status."""
        self.retry_count += 1
        self.status = TaskStatus.RETRYING

    def can_retry(self) -> bool:
        """Check if task has retries remaining."""
        return self.retry_count < self.max_retries

    def to_dict(self) -> dict[str, Any]:
        """Serialize task to dictionary for checkpointing."""
        return {
            "id": self.id,
            "description": self.description,
            "file_path": self.file_path,
            "domain": self.domain,
            "status": self.status.value,
            "assigned_agent": self.assigned_agent,
            "dependencies": self.dependencies,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "escalation_level": self.escalation_level.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        """Deserialize task from dictionary."""
        return cls(
            id=data["id"],
            description=data["description"],
            file_path=data.get("file_path", ""),
            domain=data.get("domain", ""),
            status=TaskStatus(data["status"]),
            assigned_agent=data.get("assigned_agent", ""),
            dependencies=data.get("dependencies", []),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            escalation_level=EscalationLevel(data.get("escalation_level", 1)),
            created_at=datetime.fromisoformat(data["created_at"]),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at")
                else None
            ),
            error=data.get("error", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AgentInfo:
    """Metadata about a running agent."""

    id: str = field(default_factory=_new_id)
    name: str = ""
    tier: AgentTier = AgentTier.WORKER
    status: AgentStatus = AgentStatus.IDLE
    model: str = ""
    current_task: str = ""
    domain: str = ""
    created_at: datetime = field(default_factory=_utc_now)
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_tokens: int = 0


@dataclass
class ToolResult:
    """Result from a tool execution."""

    success: bool
    output: str = ""
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result from a single validation step."""

    step: ValidationStep
    passed: bool
    message: str = ""
    details: str = ""
    duration_ms: float = 0.0


@dataclass
class TrustScore:
    """Composite trust score for a generated output."""

    generation_confidence: int = 0
    validation_quality: int = 0
    risk_score: int = 0
    stability_estimate: int = 0
    intent_alignment: int = 0

    @property
    def composite(self) -> int:
        """Calculate weighted composite trust score (0-100)."""
        weights = {
            "generation_confidence": 0.20,
            "validation_quality": 0.30,
            "risk_score": 0.20,
            "stability_estimate": 0.15,
            "intent_alignment": 0.15,
        }
        score = (
            self.generation_confidence * weights["generation_confidence"]
            + self.validation_quality * weights["validation_quality"]
            + (100 - self.risk_score) * weights["risk_score"]
            + self.stability_estimate * weights["stability_estimate"]
            + self.intent_alignment * weights["intent_alignment"]
        )
        return int(score)

    @property
    def band(self) -> TrustBand:
        """Get trust band from composite score."""
        c = self.composite
        if c >= 85:
            return TrustBand.HIGH
        if c >= 60:
            return TrustBand.MEDIUM
        if c >= 40:
            return TrustBand.LOW
        return TrustBand.CRITICAL


@dataclass
class ResourceSnapshot:
    """System resource usage snapshot."""

    vram_used_gb: float = 0.0
    vram_total_gb: float = 0.0
    ram_used_gb: float = 0.0
    ram_total_gb: float = 0.0
    cpu_percent: float = 0.0
    active_models: list[str] = field(default_factory=list)
