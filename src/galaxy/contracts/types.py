"""Contract and chunk types — structured execution contracts.

Defines the formal specifications that Domain agents output and
Workers consume. This replaces free-form description prompts with
precise, schema-driven contracts.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ─── Enums ───────────────────────────────────────────────────────────────────


class ChunkOperation(str, Enum):
    """Operations a code chunk can perform."""

    CREATE_FILE = "create_file"
    CREATE_FUNCTION = "create_function"
    CREATE_CLASS = "create_class"
    CREATE_METHOD = "create_method"
    MODIFY_FUNCTION = "modify_function"
    MODIFY_CLASS = "modify_class"
    ADD_IMPORT = "add_import"
    ADD_DECORATOR = "add_decorator"
    ADD_CONSTANT = "add_constant"
    APPEND_CODE = "append_code"


class ContractStatus(str, Enum):
    """Lifecycle states for an execution contract."""

    DRAFT = "draft"
    READY = "ready"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

    def is_terminal(self) -> bool:
        return self in (ContractStatus.COMPLETED, ContractStatus.FAILED)


class ChunkStatus(str, Enum):
    """Lifecycle states for a code chunk."""

    PENDING = "pending"
    GENERATED = "generated"
    MERGED = "merged"
    CONFLICT = "conflict"
    FAILED = "failed"

    def is_terminal(self) -> bool:
        return self in (ChunkStatus.MERGED, ChunkStatus.FAILED)


class ConstraintLevel(str, Enum):
    """Security/quality constraint levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ─── Data Models ─────────────────────────────────────────────────────────────


@dataclass
class ParameterSpec:
    """Specification for a function/method parameter."""

    name: str = ""
    type_hint: str = "Any"
    default: str | None = None  # None = required, string = default value
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type_hint": self.type_hint,
            "default": self.default,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ParameterSpec:
        return cls(
            name=data.get("name", ""),
            type_hint=data.get("type_hint", "Any"),
            default=data.get("default"),
            description=data.get("description", ""),
        )


@dataclass
class ReturnSpec:
    """Specification for a function return value."""

    type_hint: str = "None"
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"type_hint": self.type_hint, "description": self.description}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReturnSpec:
        return cls(
            type_hint=data.get("type_hint", "None"),
            description=data.get("description", ""),
        )


@dataclass
class ExecutionContract:
    """A formal contract from Domain agent → Worker.

    Instead of a free-form description, domains now output precise specs
    with signatures, parameters, return types, constraints, and validation.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    domain: str = ""                          # Domain that created this contract
    target_file: str = ""                     # Target file path
    function_name: str = ""                   # Function/class name
    operation: ChunkOperation = ChunkOperation.CREATE_FUNCTION
    description: str = ""                     # What this code should do
    parameters: list[ParameterSpec] = field(default_factory=list)
    return_spec: ReturnSpec = field(default_factory=ReturnSpec)
    dependencies: list[str] = field(default_factory=list)  # Import dependencies
    constraints: dict[str, str] = field(default_factory=dict)  # e.g. {"security": "high"}
    validation: list[str] = field(default_factory=list)  # Expected behaviors/tests
    context: str = ""                         # Additional context for the worker
    status: ContractStatus = ContractStatus.DRAFT
    worker_id: str | None = None              # Assigned worker
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def signature(self) -> str:
        """Generate the function signature string."""
        params = []
        for p in self.parameters:
            part = f"{p.name}: {p.type_hint}"
            if p.default is not None:
                part += f" = {p.default}"
            params.append(part)
        param_str = ", ".join(params)
        return f"{self.function_name}({param_str}) -> {self.return_spec.type_hint}"

    def assign(self, worker_id: str) -> None:
        """Assign this contract to a worker."""
        self.worker_id = worker_id
        self.status = ContractStatus.ASSIGNED

    def complete(self) -> None:
        """Mark as completed."""
        self.status = ContractStatus.COMPLETED

    def fail(self) -> None:
        """Mark as failed."""
        self.status = ContractStatus.FAILED

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "domain": self.domain,
            "target_file": self.target_file,
            "function_name": self.function_name,
            "operation": self.operation.value,
            "description": self.description,
            "parameters": [p.to_dict() for p in self.parameters],
            "return_spec": self.return_spec.to_dict(),
            "dependencies": self.dependencies,
            "constraints": self.constraints,
            "validation": self.validation,
            "context": self.context,
            "status": self.status.value,
            "worker_id": self.worker_id,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionContract:
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            domain=data.get("domain", ""),
            target_file=data.get("target_file", ""),
            function_name=data.get("function_name", ""),
            operation=ChunkOperation(data.get("operation", "create_function")),
            description=data.get("description", ""),
            parameters=[ParameterSpec.from_dict(p) for p in data.get("parameters", [])],
            return_spec=ReturnSpec.from_dict(data.get("return_spec", {})),
            dependencies=data.get("dependencies", []),
            constraints=data.get("constraints", {}),
            validation=data.get("validation", []),
            context=data.get("context", ""),
            status=ContractStatus(data.get("status", "draft")),
            worker_id=data.get("worker_id"),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if "created_at" in data
                else datetime.now(timezone.utc)
            ),
        )

    def to_worker_prompt(self) -> str:
        """Generate a precise prompt for the worker from this contract.

        This replaces the old free-form description prompt with a
        structured, unambiguous specification.
        """
        lines = [
            f"Generate code for: {self.function_name}",
            f"File: {self.target_file}",
            f"Operation: {self.operation.value}",
            f"Signature: {self.signature}",
            "",
            f"Description: {self.description}",
        ]

        if self.parameters:
            lines.append("\nParameters:")
            for p in self.parameters:
                req = "required" if p.default is None else f"default={p.default}"
                lines.append(f"  - {p.name} ({p.type_hint}): {p.description} [{req}]")

        lines.append(f"\nReturn: {self.return_spec.type_hint} — {self.return_spec.description}")

        if self.dependencies:
            lines.append(f"\nImports needed: {', '.join(self.dependencies)}")

        if self.constraints:
            lines.append("\nConstraints:")
            for k, v in self.constraints.items():
                lines.append(f"  - {k}: {v}")

        if self.validation:
            lines.append("\nExpected behavior:")
            for v in self.validation:
                lines.append(f"  - {v}")

        if self.context:
            lines.append(f"\nContext: {self.context}")

        lines.append("\nGenerate ONLY the code. No explanations, no markdown fences.")
        return "\n".join(lines)


@dataclass
class CodeChunk:
    """A generated code chunk from a Worker.

    Workers output these instead of full files. The Integrator
    merges chunks into complete files.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    contract_id: str = ""                     # Contract that generated this
    target_file: str = ""                     # Target file path
    target_symbol: str = ""                   # Function/class name
    operation: ChunkOperation = ChunkOperation.CREATE_FUNCTION
    content: str = ""                         # The generated code
    dependencies: list[str] = field(default_factory=list)
    status: ChunkStatus = ChunkStatus.PENDING
    worker_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "target_file": self.target_file,
            "target_symbol": self.target_symbol,
            "operation": self.operation.value,
            "content": self.content,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "worker_id": self.worker_id,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CodeChunk:
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            contract_id=data.get("contract_id", ""),
            target_file=data.get("target_file", ""),
            target_symbol=data.get("target_symbol", ""),
            operation=ChunkOperation(data.get("operation", "create_function")),
            content=data.get("content", ""),
            dependencies=data.get("dependencies", []),
            status=ChunkStatus(data.get("status", "pending")),
            worker_id=data.get("worker_id", ""),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if "created_at" in data
                else datetime.now(timezone.utc)
            ),
        )
