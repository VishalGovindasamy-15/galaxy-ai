"""Integrator types — merge operations and file state tracking."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class MergeStrategy(str, Enum):
    """How to handle merging a chunk into a file."""

    APPEND = "append"           # Append to end of file
    INSERT_BEFORE = "insert_before"  # Insert before a symbol
    INSERT_AFTER = "insert_after"    # Insert after a symbol
    REPLACE = "replace"         # Replace an existing symbol
    PREPEND = "prepend"         # Prepend (e.g., imports)


class ConflictType(str, Enum):
    """Types of merge conflicts."""

    DUPLICATE_SYMBOL = "duplicate_symbol"
    IMPORT_CONFLICT = "import_conflict"
    SIGNATURE_MISMATCH = "signature_mismatch"
    DEPENDENCY_MISSING = "dependency_missing"


class ConflictResolution(str, Enum):
    """How a conflict was resolved."""

    KEEP_EXISTING = "keep_existing"
    USE_NEW = "use_new"
    MERGE_BOTH = "merge_both"
    MANUAL = "manual"


@dataclass
class FileState:
    """Tracks the current state of a file being assembled from chunks."""

    path: str = ""
    content: str = ""
    imports: list[str] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)  # Functions/classes defined
    chunk_ids: list[str] = field(default_factory=list)  # Chunks merged into this file
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def has_symbol(self, name: str) -> bool:
        """Check if a symbol already exists in this file."""
        return name in self.symbols

    def add_symbol(self, name: str) -> None:
        """Register a new symbol."""
        if name not in self.symbols:
            self.symbols.append(name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "content": self.content,
            "imports": self.imports,
            "symbols": self.symbols,
            "chunk_ids": self.chunk_ids,
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FileState:
        return cls(
            path=data.get("path", ""),
            content=data.get("content", ""),
            imports=data.get("imports", []),
            symbols=data.get("symbols", []),
            chunk_ids=data.get("chunk_ids", []),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if "updated_at" in data
                else datetime.now(timezone.utc)
            ),
        )


@dataclass
class ConflictInfo:
    """Information about a merge conflict."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    conflict_type: ConflictType = ConflictType.DUPLICATE_SYMBOL
    file_path: str = ""
    symbol_name: str = ""
    existing_content: str = ""
    new_content: str = ""
    resolution: ConflictResolution | None = None
    resolved_content: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def resolve(self, resolution: ConflictResolution, content: str = "") -> None:
        """Resolve this conflict."""
        self.resolution = resolution
        self.resolved_content = content

    @property
    def is_resolved(self) -> bool:
        return self.resolution is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "conflict_type": self.conflict_type.value,
            "file_path": self.file_path,
            "symbol_name": self.symbol_name,
            "resolution": self.resolution.value if self.resolution else None,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class MergeResult:
    """Result of a merge operation."""

    success: bool = True
    file_path: str = ""
    content: str = ""
    conflicts: list[ConflictInfo] = field(default_factory=list)
    chunks_merged: int = 0
    symbols_added: list[str] = field(default_factory=list)
    imports_added: list[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0
