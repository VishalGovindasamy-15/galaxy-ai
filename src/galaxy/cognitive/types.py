"""Cognitive pipeline types — modes, stages, and pipeline state.

Defines the data structures for Galaxy's multi-stage cognitive pipeline
that transforms vague prompts into precise engineering plans.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class CognitiveMode(str, Enum):
    """Execution modes for the cognitive pipeline."""

    NORMAL = "normal"       # Direct planning — fast, cheap, single LLM call
    REASONING = "reasoning"  # Deep pipeline — Expand → Plan → Retrieve → Reflect → Synthesize

    @property
    def description(self) -> str:
        descriptions = {
            "normal": "Fast mode — direct planning, single pass",
            "reasoning": "Deep mode — multi-stage cognitive pipeline",
        }
        return descriptions.get(self.value, self.value)


class PipelineStage(str, Enum):
    """Stages in the reasoning cognitive pipeline."""

    EXPAND = "expand"         # Vague prompt → structured engineering spec
    PLAN = "plan"             # Spec → dependency-aware DAG
    RETRIEVE = "retrieve"     # Fetch relevant context (docs, code, memory)
    REFLECT = "reflect"       # Critique and verify the plan
    SYNTHESIZE = "synthesize"  # Merge reasoning into final plan

    @property
    def order(self) -> int:
        return list(PipelineStage).index(self)


class StageStatus(str, Enum):
    """Status of a pipeline stage."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

    def is_terminal(self) -> bool:
        return self in (StageStatus.COMPLETED, StageStatus.FAILED, StageStatus.SKIPPED)


# ─── Data Models ─────────────────────────────────────────────────────────────


@dataclass
class StageResult:
    """Result from a single pipeline stage."""

    stage: PipelineStage = PipelineStage.EXPAND
    status: StageStatus = StageStatus.PENDING
    input_data: str = ""
    output_data: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    error: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def complete(self, output: str, duration_ms: float = 0.0) -> None:
        self.status = StageStatus.COMPLETED
        self.output_data = output
        self.duration_ms = duration_ms

    def fail(self, error: str) -> None:
        self.status = StageStatus.FAILED
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage.value,
            "status": self.status.value,
            "input_data": self.input_data[:200],  # Truncate for storage
            "output_data": self.output_data[:500],
            "metadata": self.metadata,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ExpandedSpec:
    """Output of the Expander stage — structured engineering specification."""

    original_prompt: str = ""
    project_type: str = ""  # e.g. "REST API", "CLI tool", "web app"
    tech_stack: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    non_functional: list[str] = field(default_factory=list)  # Performance, security, etc.
    domains: list[str] = field(default_factory=list)  # Suggested domain splits
    ambiguities: list[str] = field(default_factory=list)  # Things that need clarification

    def to_prompt(self) -> str:
        """Convert spec to a structured prompt for downstream stages."""
        lines = [
            f"Project Type: {self.project_type}",
            f"Tech Stack: {', '.join(self.tech_stack)}",
            "",
            "Features:",
        ]
        for f in self.features:
            lines.append(f"  - {f}")
        if self.constraints:
            lines.append("\nConstraints:")
            for c in self.constraints:
                lines.append(f"  - {c}")
        if self.non_functional:
            lines.append("\nNon-Functional Requirements:")
            for nf in self.non_functional:
                lines.append(f"  - {nf}")
        if self.domains:
            lines.append(f"\nDomains: {', '.join(self.domains)}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_prompt": self.original_prompt,
            "project_type": self.project_type,
            "tech_stack": self.tech_stack,
            "features": self.features,
            "constraints": self.constraints,
            "non_functional": self.non_functional,
            "domains": self.domains,
            "ambiguities": self.ambiguities,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExpandedSpec:
        return cls(
            original_prompt=data.get("original_prompt", ""),
            project_type=data.get("project_type", ""),
            tech_stack=data.get("tech_stack", []),
            features=data.get("features", []),
            constraints=data.get("constraints", []),
            non_functional=data.get("non_functional", []),
            domains=data.get("domains", []),
            ambiguities=data.get("ambiguities", []),
        )


@dataclass
class PlanNode:
    """A single node in the dependency-aware plan DAG."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    domain: str = ""
    description: str = ""
    dependencies: list[str] = field(default_factory=list)  # IDs of nodes this depends on
    priority: int = 0
    estimated_chunks: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "domain": self.domain,
            "description": self.description,
            "dependencies": self.dependencies,
            "priority": self.priority,
            "estimated_chunks": self.estimated_chunks,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlanNode:
        return cls(
            id=data.get("id", uuid.uuid4().hex[:8]),
            name=data.get("name", ""),
            domain=data.get("domain", ""),
            description=data.get("description", ""),
            dependencies=data.get("dependencies", []),
            priority=data.get("priority", 0),
            estimated_chunks=data.get("estimated_chunks", 1),
        )


@dataclass
class ExecutionPlan:
    """Output of the Planner stage — a dependency-aware execution DAG."""

    nodes: list[PlanNode] = field(default_factory=list)
    execution_order: list[str] = field(default_factory=list)  # Node IDs in topological order
    domains: list[str] = field(default_factory=list)
    estimated_total_chunks: int = 0

    def get_node(self, node_id: str) -> PlanNode | None:
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_roots(self) -> list[PlanNode]:
        """Get nodes with no dependencies (can start immediately)."""
        return [n for n in self.nodes if not n.dependencies]

    def get_dependents(self, node_id: str) -> list[PlanNode]:
        """Get nodes that depend on a given node."""
        return [n for n in self.nodes if node_id in n.dependencies]

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "execution_order": self.execution_order,
            "domains": self.domains,
            "estimated_total_chunks": self.estimated_total_chunks,
        }


@dataclass
class RetrievedContext:
    """Output of the Retriever stage — gathered context."""

    relevant_files: list[str] = field(default_factory=list)
    code_snippets: list[str] = field(default_factory=list)
    documentation: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)  # Detected patterns/conventions
    memory_items: list[str] = field(default_factory=list)

    def to_prompt(self) -> str:
        """Format context for downstream stages."""
        parts = []
        if self.patterns:
            parts.append("Detected Patterns: " + ", ".join(self.patterns))
        if self.code_snippets:
            parts.append("Relevant Code:\n" + "\n---\n".join(self.code_snippets[:3]))
        if self.documentation:
            parts.append("Documentation:\n" + "\n".join(self.documentation[:3]))
        return "\n\n".join(parts)


@dataclass
class ReflectionResult:
    """Output of the Reflection stage — critique and verification."""

    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    missing_items: list[str] = field(default_factory=list)
    confidence: float = 0.0  # 0.0 to 1.0
    approved: bool = True

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "issues": self.issues,
            "suggestions": self.suggestions,
            "missing_items": self.missing_items,
            "confidence": self.confidence,
            "approved": self.approved,
        }


@dataclass
class PipelineState:
    """Full state of a cognitive pipeline execution."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    mode: CognitiveMode = CognitiveMode.NORMAL
    original_prompt: str = ""
    stage_results: list[StageResult] = field(default_factory=list)
    final_plan: str = ""
    total_duration_ms: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def current_stage(self) -> PipelineStage | None:
        for result in self.stage_results:
            if result.status == StageStatus.RUNNING:
                return result.stage
        return None

    @property
    def is_complete(self) -> bool:
        if not self.stage_results:
            return False
        return all(r.status.is_terminal() for r in self.stage_results)

    @property
    def success(self) -> bool:
        return self.is_complete and all(
            r.status != StageStatus.FAILED for r in self.stage_results
        )
