"""Conflict detection and resolution for code chunk merging."""

from __future__ import annotations

import logging
import re
from typing import Any

from galaxy.contracts.types import CodeChunk
from galaxy.integrator import ConflictInfo, ConflictResolution, ConflictType, FileState

logger = logging.getLogger(__name__)


class ConflictDetector:
    """Detects conflicts when merging code chunks into files.

    Checks for:
    - Duplicate symbol definitions
    - Import conflicts
    - Signature mismatches
    """

    def detect(self, chunk: CodeChunk, file_state: FileState) -> list[ConflictInfo]:
        """Detect all conflicts between a chunk and file state.

        Args:
            chunk: The chunk being merged.
            file_state: Current state of the target file.

        Returns:
            List of detected conflicts.
        """
        conflicts: list[ConflictInfo] = []

        # Check duplicate symbols
        if chunk.target_symbol and file_state.has_symbol(chunk.target_symbol):
            conflicts.append(ConflictInfo(
                conflict_type=ConflictType.DUPLICATE_SYMBOL,
                file_path=chunk.target_file,
                symbol_name=chunk.target_symbol,
                existing_content=self._extract_symbol_content(
                    file_state.content, chunk.target_symbol
                ),
                new_content=chunk.content,
            ))

        # Check import conflicts
        chunk_imports = self._extract_imports(chunk.content)
        for imp in chunk_imports:
            conflicting = self._find_import_conflict(imp, file_state.imports)
            if conflicting:
                conflicts.append(ConflictInfo(
                    conflict_type=ConflictType.IMPORT_CONFLICT,
                    file_path=chunk.target_file,
                    symbol_name=imp,
                    existing_content=conflicting,
                    new_content=imp,
                ))

        return conflicts

    def detect_batch(
        self, chunks: list[CodeChunk], file_state: FileState
    ) -> list[ConflictInfo]:
        """Detect conflicts across multiple chunks targeting the same file."""
        conflicts: list[ConflictInfo] = []
        seen_symbols: set[str] = set(file_state.symbols)

        for chunk in chunks:
            # Check against file state
            conflicts.extend(self.detect(chunk, file_state))

            # Check against other chunks in batch
            if chunk.target_symbol and chunk.target_symbol in seen_symbols:
                # Already reported via detect() if in file_state,
                # but also check inter-chunk duplicates
                other_chunks = [c for c in chunks if c.id != chunk.id and c.target_symbol == chunk.target_symbol]
                for other in other_chunks:
                    conflicts.append(ConflictInfo(
                        conflict_type=ConflictType.DUPLICATE_SYMBOL,
                        file_path=chunk.target_file,
                        symbol_name=chunk.target_symbol,
                        existing_content=other.content,
                        new_content=chunk.content,
                    ))

            if chunk.target_symbol:
                seen_symbols.add(chunk.target_symbol)

        # Deduplicate by symbol name
        seen_ids: set[str] = set()
        unique: list[ConflictInfo] = []
        for c in conflicts:
            key = f"{c.conflict_type.value}:{c.symbol_name}"
            if key not in seen_ids:
                seen_ids.add(key)
                unique.append(c)

        return unique

    def _extract_symbol_content(self, content: str, symbol: str) -> str:
        """Extract the content of a symbol from file content."""
        pattern = rf"(^(?:async\s+)?def\s+{re.escape(symbol)}\s*\(|^class\s+{re.escape(symbol)}[\s(:])"
        match = re.search(pattern, content, re.MULTILINE)
        if not match:
            return ""

        start = match.start()
        rest = content[match.end():]
        next_match = re.search(r"^(?:def |async def |class )\w+", rest, re.MULTILINE)
        if next_match:
            end = match.end() + next_match.start()
        else:
            end = len(content)

        return content[start:end].rstrip()

    def _extract_imports(self, content: str) -> list[str]:
        """Extract import lines from content."""
        imports = []
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                imports.append(stripped)
        return imports

    def _find_import_conflict(self, new_import: str, existing_imports: list[str]) -> str | None:
        """Check if an import conflicts with existing imports.

        Conflicts: same module, different names imported.
        """
        new_parts = self._parse_import(new_import)
        if not new_parts:
            return None

        for existing in existing_imports:
            existing_parts = self._parse_import(existing)
            if not existing_parts:
                continue

            # Same module but different import → conflict
            if (new_parts["module"] == existing_parts["module"]
                    and new_parts["names"] != existing_parts["names"]
                    and new_parts.get("is_from") and existing_parts.get("is_from")):
                return existing

        return None

    def _parse_import(self, import_str: str) -> dict[str, Any] | None:
        """Parse an import statement into components."""
        import_str = import_str.strip()

        from_match = re.match(r"from\s+(\S+)\s+import\s+(.+)", import_str)
        if from_match:
            return {
                "module": from_match.group(1),
                "names": set(n.strip() for n in from_match.group(2).split(",")),
                "is_from": True,
            }

        plain_match = re.match(r"import\s+(\S+)", import_str)
        if plain_match:
            return {
                "module": plain_match.group(1),
                "names": {plain_match.group(1)},
                "is_from": False,
            }

        return None


class ConflictResolver:
    """Resolves merge conflicts using configurable strategies."""

    def resolve(
        self,
        conflict: ConflictInfo,
        strategy: ConflictResolution = ConflictResolution.USE_NEW,
    ) -> str:
        """Resolve a conflict and return the resolved content.

        Args:
            conflict: The conflict to resolve.
            strategy: Resolution strategy.

        Returns:
            The resolved content string.
        """
        if strategy == ConflictResolution.KEEP_EXISTING:
            resolved = conflict.existing_content
        elif strategy == ConflictResolution.USE_NEW:
            resolved = conflict.new_content
        elif strategy == ConflictResolution.MERGE_BOTH:
            resolved = self._merge_both(conflict)
        else:
            resolved = conflict.new_content  # Default to new

        conflict.resolve(strategy, resolved)
        return resolved

    def auto_resolve(self, conflict: ConflictInfo) -> str:
        """Auto-resolve a conflict based on its type.

        - DUPLICATE_SYMBOL: use new (overwrite)
        - IMPORT_CONFLICT: merge both imports
        - SIGNATURE_MISMATCH: use new
        - DEPENDENCY_MISSING: use new
        """
        if conflict.conflict_type == ConflictType.IMPORT_CONFLICT:
            return self.resolve(conflict, ConflictResolution.MERGE_BOTH)
        return self.resolve(conflict, ConflictResolution.USE_NEW)

    def _merge_both(self, conflict: ConflictInfo) -> str:
        """Merge both contents together."""
        if conflict.conflict_type == ConflictType.IMPORT_CONFLICT:
            return self._merge_imports(conflict.existing_content, conflict.new_content)
        # For other types, concatenate
        return conflict.existing_content + "\n\n" + conflict.new_content

    def _merge_imports(self, existing: str, new: str) -> str:
        """Merge two import statements from the same module."""
        existing_match = re.match(r"from\s+(\S+)\s+import\s+(.+)", existing)
        new_match = re.match(r"from\s+(\S+)\s+import\s+(.+)", new)

        if existing_match and new_match and existing_match.group(1) == new_match.group(1):
            module = existing_match.group(1)
            names = set()
            names.update(n.strip() for n in existing_match.group(2).split(","))
            names.update(n.strip() for n in new_match.group(2).split(","))
            return f"from {module} import {', '.join(sorted(names))}"

        return new  # Can't merge, use new
