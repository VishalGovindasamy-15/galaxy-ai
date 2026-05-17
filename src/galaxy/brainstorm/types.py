"""Brainstorm data types — models for the brainstorming engine.

Defines the core data structures for Galaxy's pre-execution cognitive layer:
- Ideas (temp and permanent)
- Brainstorm sessions
- Decision records with full audit trail
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ─── Enums ───────────────────────────────────────────────────────────────────


class IdeaStatus(str, Enum):
    """Lifecycle states for an idea."""

    DRAFT = "draft"           # Just captured, not yet evaluated
    EXPLORING = "exploring"   # Being discussed/refined
    APPROVED = "approved"     # User approved → promoted to permanent
    REJECTED = "rejected"     # User rejected
    DEFERRED = "deferred"     # Postponed for later consideration
    MERGED = "merged"         # Combined into another idea

    def is_terminal(self) -> bool:
        """Return True if this status is final."""
        return self in (
            IdeaStatus.APPROVED,
            IdeaStatus.REJECTED,
            IdeaStatus.MERGED,
        )

    def is_active(self) -> bool:
        """Return True if this idea is still being explored."""
        return self in (IdeaStatus.DRAFT, IdeaStatus.EXPLORING)


class IdeaCategory(str, Enum):
    """Categories for classifying ideas."""

    FEATURE = "feature"
    ARCHITECTURE = "architecture"
    CONSTRAINT = "constraint"
    DEPENDENCY = "dependency"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTING = "testing"
    DEVOPS = "devops"
    UI_UX = "ui_ux"
    OTHER = "other"


class BrainstormMode(str, Enum):
    """Brainstorming session modes."""

    FREE_FORM = "free_form"       # Open-ended exploration
    STRUCTURED = "structured"     # Guided with prompts/questions
    GUIDED = "guided"             # Master leads with suggestions

    @property
    def description(self) -> str:
        """Human-readable description of this mode."""
        descriptions = {
            "free_form": "Open-ended exploration — say anything",
            "structured": "Guided with prompts and questions",
            "guided": "Master leads with suggestions and trade-offs",
        }
        return descriptions.get(self.value, self.value)


class BrainstormPhase(str, Enum):
    """Phases of a brainstorming session."""

    IDEATION = "ideation"       # Generating ideas
    REFINEMENT = "refinement"   # Refining and detailing ideas
    EVALUATION = "evaluation"   # Evaluating and scoring ideas
    APPROVAL = "approval"       # User approves/rejects ideas
    COMPLETE = "complete"       # Session finished


class DecisionType(str, Enum):
    """Types of decisions recorded in the decision log."""

    IDEA_CREATED = "idea_created"
    IDEA_UPDATED = "idea_updated"
    IDEA_APPROVED = "idea_approved"
    IDEA_REJECTED = "idea_rejected"
    IDEA_DEFERRED = "idea_deferred"
    IDEA_MERGED = "idea_merged"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    PHASE_CHANGED = "phase_changed"
    CONSTRAINT_ADDED = "constraint_added"
    ARCHITECTURE_DECISION = "architecture_decision"


# ─── Data Models ─────────────────────────────────────────────────────────────


@dataclass
class Idea:
    """A single brainstorming idea.

    Ideas start as DRAFT in the temp store. When the user approves,
    they're promoted to APPROVED and moved to the permanent store.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""
    description: str = ""
    category: IdeaCategory = IdeaCategory.FEATURE
    status: IdeaStatus = IdeaStatus.DRAFT
    priority: int = 0  # 0 = unset, 1 = highest, 5 = lowest
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)  # IDs of ideas this depends on
    parent_id: str | None = None  # If merged into another idea
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def approve(self) -> None:
        """Mark this idea as approved."""
        self.status = IdeaStatus.APPROVED
        self.updated_at = datetime.now(timezone.utc)

    def reject(self) -> None:
        """Mark this idea as rejected."""
        self.status = IdeaStatus.REJECTED
        self.updated_at = datetime.now(timezone.utc)

    def defer(self) -> None:
        """Mark this idea as deferred."""
        self.status = IdeaStatus.DEFERRED
        self.updated_at = datetime.now(timezone.utc)

    def merge_into(self, parent_id: str) -> None:
        """Mark this idea as merged into another."""
        self.status = IdeaStatus.MERGED
        self.parent_id = parent_id
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for YAML/JSON storage."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "status": self.status.value,
            "priority": self.priority,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "parent_id": self.parent_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Idea:
        """Deserialize from dictionary."""
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            title=data.get("title", ""),
            description=data.get("description", ""),
            category=IdeaCategory(data.get("category", "feature")),
            status=IdeaStatus(data.get("status", "draft")),
            priority=data.get("priority", 0),
            tags=data.get("tags", []),
            dependencies=data.get("dependencies", []),
            parent_id=data.get("parent_id"),
            metadata=data.get("metadata", {}),
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
class DecisionRecord:
    """A single decision in the brainstorming log.

    Every action during brainstorming is recorded with timestamp,
    reason, and context for full audit trail.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    decision_type: DecisionType = DecisionType.IDEA_CREATED
    idea_id: str | None = None
    description: str = ""
    reason: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "decision_type": self.decision_type.value,
            "idea_id": self.idea_id,
            "description": self.description,
            "reason": self.reason,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DecisionRecord:
        """Deserialize from dictionary."""
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            decision_type=DecisionType(data.get("decision_type", "idea_created")),
            idea_id=data.get("idea_id"),
            description=data.get("description", ""),
            reason=data.get("reason", ""),
            context=data.get("context", {}),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data
                else datetime.now(timezone.utc)
            ),
        )


@dataclass
class BrainstormSession:
    """A brainstorming session with its state.

    Tracks the current phase, mode, and all ideas generated during
    this session. Sessions can be saved and resumed.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    project_name: str = ""
    prompt: str = ""
    mode: BrainstormMode = BrainstormMode.STRUCTURED
    phase: BrainstormPhase = BrainstormPhase.IDEATION
    idea_ids: list[str] = field(default_factory=list)  # IDs of all ideas in this session
    decision_ids: list[str] = field(default_factory=list)  # IDs of decisions made
    config: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def advance_phase(self) -> BrainstormPhase:
        """Advance to the next phase. Returns the new phase."""
        phase_order = list(BrainstormPhase)
        current_idx = phase_order.index(self.phase)
        if current_idx < len(phase_order) - 1:
            self.phase = phase_order[current_idx + 1]
        self.updated_at = datetime.now(timezone.utc)
        return self.phase

    @property
    def is_complete(self) -> bool:
        """Return True if this session is finished."""
        return self.phase == BrainstormPhase.COMPLETE

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "project_name": self.project_name,
            "prompt": self.prompt,
            "mode": self.mode.value,
            "phase": self.phase.value,
            "idea_ids": self.idea_ids,
            "decision_ids": self.decision_ids,
            "config": self.config,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BrainstormSession:
        """Deserialize from dictionary."""
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            project_name=data.get("project_name", ""),
            prompt=data.get("prompt", ""),
            mode=BrainstormMode(data.get("mode", "structured")),
            phase=BrainstormPhase(data.get("phase", "ideation")),
            idea_ids=data.get("idea_ids", []),
            decision_ids=data.get("decision_ids", []),
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


@dataclass
class BrainstormSummary:
    """Summary statistics for a brainstorming session."""

    session_id: str = ""
    total_ideas: int = 0
    approved_ideas: int = 0
    rejected_ideas: int = 0
    deferred_ideas: int = 0
    pending_ideas: int = 0
    total_decisions: int = 0
    categories: dict[str, int] = field(default_factory=dict)
    duration_seconds: float = 0.0
